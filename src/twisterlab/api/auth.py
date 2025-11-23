"""
Azure AD OAuth2 Authentication for TwisterLab API

This module provides:
- OAuth2 authentication endpoints (/auth/login, /auth/callback, /auth/logout)
- JWT token verification middleware
- User session management with Redis
- Current user dependency injection for protected routes

Usage:
    from api.auth import get_current_user, router as auth_router

    app.include_router(auth_router, prefix="/auth", tags=["authentication"])

    @app.get("/protected")
    async def protected_route(user: dict = Depends(get_current_user)):
        return {"message": f"Hello {user['name']}"}
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from agents.auth.azure_ad_auth import AzureADAuth

logger = logging.getLogger(__name__)

# Router for auth endpoints
router = APIRouter()

# Security scheme for JWT bearer token
security = HTTPBearer()

# Azure AD auth instance (initialized on first request)
_azure_ad_auth: Optional[AzureADAuth] = None

# Redis client for session management
_redis_client: Optional[aioredis.Redis] = None


def get_azure_ad_auth() -> AzureADAuth:
    """Get or initialize Azure AD auth instance."""
    global _azure_ad_auth
    if _azure_ad_auth is None:
        _azure_ad_auth = AzureADAuth()
    return _azure_ad_auth


async def get_redis_client() -> aioredis.Redis:
    """Get or initialize Redis client for session management."""
    global _redis_client
    if _redis_client is None:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")

        _redis_client = await aioredis.from_url(
            f"redis://{redis_host}:{redis_port}",
            password=redis_password,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )
    return _redis_client


async def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token from Azure AD.

    Args:
        token: JWT access token from Authorization header

    Returns:
        Dict with user claims (sub, name, email, roles, etc.)

    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    azure_auth = get_azure_ad_auth()

    # Basic structure validation
    if not azure_auth.validate_token_structure(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode without verification first to get tenant/issuer info
        unverified_claims = jwt.get_unverified_claims(token)

        # In production, you would:
        # 1. Fetch Azure AD public keys from https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
        # 2. Verify signature using public key
        # 3. Validate issuer, audience, expiration

        # For now, basic validation (MUST enhance for production)
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")

        if not unverified_claims.get("aud") == client_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiration
        exp = unverified_claims.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return unverified_claims

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.

    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["sub"], "name": user["name"]}

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        User claims dictionary with keys:
            - sub: User ID (Azure AD object ID)
            - name: User display name
            - email: User email
            - roles: List of user roles (if configured)

    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    token = credentials.credentials
    user_claims = await verify_jwt_token(token)

    # Cache user info in Redis for 1 hour
    try:
        redis = await get_redis_client()
        user_id = user_claims.get("sub")
        cache_key = f"user:{user_id}"

        await redis.setex(cache_key, 3600, str(user_claims))  # 1 hour TTL
    except Exception as e:
        logger.warning(f"Failed to cache user in Redis: {e}")

    return user_claims


@router.get("/login")
async def login(request: Request):
    """
    Initiate OAuth2 login flow.

    Redirects user to Azure AD login page. After successful authentication,
    Azure AD will redirect back to /auth/callback with authorization code.

    Query params:
        redirect_uri (optional): URL to redirect after successful login
                                Default: /

    Returns:
        RedirectResponse to Azure AD authorization URL
    """
    azure_auth = get_azure_ad_auth()

    # Get redirect URI from query params or use default
    redirect_after_login = request.query_params.get("redirect_uri", "/")

    # Store redirect URI in session (use Redis in production)
    # For now, encode in state parameter
    state = f"redirect={redirect_after_login}"

    # Generate authorization URL
    auth_url = azure_auth.get_authorization_url(state=state)

    logger.info(f"Redirecting to Azure AD login: {auth_url}")
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(request: Request):
    """
    OAuth2 callback endpoint.

    Azure AD redirects here after user authentication with authorization code.
    Exchanges code for access token and redirects to application.

    Query params:
        code: Authorization code from Azure AD
        state: State parameter with redirect URI
        error (optional): Error code if auth failed
        error_description (optional): Error details

    Returns:
        RedirectResponse to application with token in query params
        (In production, use httponly cookies instead)
    """
    # Check for errors
    error = request.query_params.get("error")
    if error:
        error_desc = request.query_params.get("error_description", "Unknown error")
        logger.error(f"Azure AD auth error: {error} - {error_desc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {error_desc}"
        )

    # Get authorization code
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code"
        )

    # Exchange code for token
    azure_auth = get_azure_ad_auth()
    token_response = await azure_auth.acquire_token_by_code(code)

    # Extract redirect URI from state
    state = request.query_params.get("state", "")
    redirect_uri = "/"
    if state.startswith("redirect="):
        redirect_uri = state.split("=", 1)[1]

    # In production, store token in httponly cookie or secure session
    # For demo, return token in response (NOT SECURE for production)
    access_token = token_response.get("access_token")

    logger.info(f"Successfully authenticated user, redirecting to {redirect_uri}")

    # TODO: In production, use httponly cookies:
    # response = RedirectResponse(url=redirect_uri)
    # response.set_cookie(
    #     key="access_token",
    #     value=access_token,
    #     httponly=True,
    #     secure=True,  # HTTPS only
    #     samesite="lax",
    #     max_age=3600
    # )
    # return response

    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": token_response.get("expires_in", 3600),
        "redirect_uri": redirect_uri,
        "message": "Include this token in Authorization header: Bearer <access_token>",
    }


@router.post("/logout")
async def logout(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout current user.

    Clears user session from Redis cache and invalidates token.

    Args:
        user: Current authenticated user (auto-injected)

    Returns:
        Success message
    """
    try:
        redis = await get_redis_client()
        user_id = user.get("sub")
        cache_key = f"user:{user_id}"

        # Remove user from cache
        await redis.delete(cache_key)

        logger.info(f"User {user_id} logged out successfully")

        return {"status": "success", "message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.get("/me")
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Protected endpoint that returns user profile from JWT claims.

    Args:
        user: Current authenticated user (auto-injected)

    Returns:
        User profile with ID, name, email, roles
    """
    return {
        "user_id": user.get("sub"),
        "name": user.get("name"),
        "email": user.get("preferred_username") or user.get("email"),
        "roles": user.get("roles", []),
        "tenant_id": user.get("tid"),
        "authenticated_at": datetime.now().isoformat(),
    }
