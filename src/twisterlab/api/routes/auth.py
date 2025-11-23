"""
SSO/LDAP Authentication Routes for TwisterLab API
Provides authentication endpoints for Continue IDE and all TwisterLab modules
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

# Import SSO manager (will create if not exists)
try:
    from api.auth.sso_ldap import (
        get_current_user as sso_get_current_user,
        login_endpoint,
        logout_endpoint,
        me_endpoint,
        require_role,
        sso_manager,
    )

    SSO_AVAILABLE = True
except ImportError:
    SSO_AVAILABLE = False
    logging.warning("SSO/LDAP module not available")

logger = logging.getLogger(__name__)

# Create auth router
router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    """Login request model"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response model"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class UserResponse(BaseModel):
    """User information response"""

    username: str
    email: str | None
    display_name: str
    roles: list[str]


# Authentication endpoints
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with LDAP and return JWT token

    Example:
        POST /auth/login
        {
            "username": "john.doe",
            "password": "SecurePassword123"
        }

    Returns:
        {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {...}
        }
    """
    if not SSO_AVAILABLE:
        # Fallback to mock authentication for testing
        logger.warning("SSO not available, using mock authentication")
        return {
            "access_token": "mock-token-" + request.username,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "username": request.username,
                "email": f"{request.username}@twisterlab.local",
                "display_name": request.username.title(),
                "roles": ["user"],
            },
        }

    return await login_endpoint(request.username, request.password)


@router.post("/logout")
async def logout(
    user: Dict = Depends(get_current_user if SSO_AVAILABLE else lambda: {}),
):
    """
    Logout current user and invalidate session

    Requires: Bearer token in Authorization header

    Returns:
        {"message": "Logged out successfully"}
    """
    if not SSO_AVAILABLE:
        return {"message": "Logged out successfully (mock)"}

    return await logout_endpoint(user)


try:
    from api.auth_hybrid import get_current_user as hybrid_get_current_user

    auth_dep = Depends(hybrid_get_current_user)
except Exception:
    try:
        from api.auth import get_current_user as api_get_current_user

        auth_dep = Depends(api_get_current_user)
    except Exception:
        auth_dep = Depends(lambda: {})


@router.get("/me", response_model=UserResponse)
async def get_me(request: Request, user: Dict = auth_dep):
    """
    Get current authenticated user information

    Requires: Bearer token in Authorization header

    Returns:
        {
            "username": "john.doe",
            "email": "john.doe@twisterlab.local",
            "display_name": "John Doe",
            "roles": ["admin", "operator"]
        }
    """
    # Prefer hybrid auth dependency if present for strict checks (Bearer token)
    # If hybrid_get_current_user is used as dependency, FastAPI will enforce token validation
    if user:
        return {
            "user_id": user.get("sub") or user.get("username"),
            "username": user.get("username") or user.get("sub"),
            "email": user.get("email") or user.get("preferred_username"),
            "display_name": user.get("display_name", user.get("username", "")),
            "roles": user.get("roles", []),
        }
    # If Authorization header is present, try to validate token using API-level verifier first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            from api.auth import verify_jwt_token as api_verify_jwt

            user_claims = await api_verify_jwt(token)
            return {
                "user_id": user_claims.get("sub") or user_claims.get("username"),
                "username": user_claims.get("username") or user_claims.get("sub"),
                "email": user_claims.get("email") or user_claims.get("preferred_username"),
                "display_name": user_claims.get("display_name", user_claims.get("username", "")),
                "roles": user_claims.get("roles", []),
            }
        except Exception:
            # Not authenticated by api-level verifier, fallthrough to hybrid/local checks
            pass

    # Fallback to local behavior when hybrid auth is not available
    if not SSO_AVAILABLE:
        return {
            "username": "mock_user",
            "email": "mock@twisterlab.local",
            "display_name": "Mock User",
            "roles": ["user"],
        }
    return await me_endpoint(user)


@router.get("/verify")
async def verify_token(authorization: str = Header(None), required_role: str | None = None):
    """
    Verify JWT token for Traefik ForwardAuth middleware

    This endpoint is called by Traefik to verify authentication
    for protected routes.

    Headers:
        Authorization: Bearer <token>

    Query Parameters:
        required_role: Optional role requirement (admin, operator, user, readonly)

    Returns:
        200 OK with user headers if valid
        401 Unauthorized if invalid
        403 Forbidden if insufficient permissions
    """
    if not SSO_AVAILABLE:
        # Mock authentication for testing
        return {
            "X-User-Id": "mock_user",
            "X-User-Email": "mock@twisterlab.local",
            "X-User-Roles": "user",
        }

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")
    user_info = sso_manager.validate_token(token)

    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Check role if required
    if required_role:
        if not sso_manager.check_permission(user_info, required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

    # Return user headers for Traefik
    return {
        "X-User-Id": user_info["sub"],
        "X-User-Email": user_info.get("email", ""),
        "X-User-Roles": ",".join(user_info.get("roles", [])),
    }


@router.get("/health")
async def auth_health():
    """
    Health check for authentication service

    Returns:
        {
            "status": "healthy",
            "sso_available": true,
            "ldap_configured": true
        }
    """
    return {
        "status": "healthy",
        "sso_available": SSO_AVAILABLE,
        "ldap_configured": SSO_AVAILABLE,
    }


# Admin-only endpoints
@router.get("/sessions")
async def list_sessions(
    user: Dict = Depends(require_role("admin") if SSO_AVAILABLE else lambda: {}),
):
    """
    List all active sessions (admin only)

    Requires: Bearer token with admin role

    Returns:
        List of active sessions
    """
    if not SSO_AVAILABLE:
        return {"sessions": []}

    return {
        "sessions": [
            {
                "username": username,
                "created_at": session["created_at"].isoformat(),
                "expires_at": session["expires_at"].isoformat(),
            }
            for username, session in sso_manager.sessions.items()
        ]
    }


@router.delete("/sessions/{username}")
async def revoke_session(
    username: str,
    user: Dict = Depends(require_role("admin") if SSO_AVAILABLE else lambda: {}),
):
    """
    Revoke a user's session (admin only)

    Requires: Bearer token with admin role

    Args:
        username: Username to revoke

    Returns:
        {"message": "Session revoked successfully"}
    """
    if not SSO_AVAILABLE:
        return {"message": f"Session revoked for {username} (mock)"}

    if sso_manager.logout(username):
        return {"message": f"Session revoked for {username}"}
    else:
        raise HTTPException(status_code=404, detail=f"No active session found for {username}")
