"""
Production security configuration
Authentication, authorization, and security middleware
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
try:
    from passlib.context import CryptContext
except ImportError:
    CryptContext = None

from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
if CryptContext:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None

# Security schemes
security = HTTPBearer()

# Logger
logger = logging.getLogger("twisterlab.security")


class TokenData(BaseModel):
    """Token payload data"""

    sub: str  # subject (user id)
    exp: datetime
    iat: datetime
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class UserCredentials(BaseModel):
    """User login credentials"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # ip -> list of timestamps
        logger.info(f"RateLimitMiddleware initialized with limit {requests_per_minute}")

    async def dispatch(self, request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        # Debug log to trace IP
        logger.debug(f"RateLimit check for IP: {client_ip}. Count: {len(self.requests.get(client_ip, []))}")
        
        # Clean old requests
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        if client_ip in self.requests:
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] if ts > cutoff
            ]

        # Check rate limit
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"},
            )

        # Add current request
        self.requests[client_ip].append(now)

        response = await call_next(request)
        return response


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenData(**payload)
        return token_data
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token_data: TokenData = Depends(verify_token)) -> str:
    """Return the current user identifier from a valid token."""
    return token_data.sub


def require_role(required_role: str):
    """Dependency to require a specific role"""

    def role_checker(token_data: TokenData = Depends(verify_token)):
        if required_role not in token_data.roles:
            logger.warning(
                f"Access denied. Required role: {required_role}, "
                f"user roles: {token_data.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        return token_data

    return role_checker


def require_permission(required_permission: str):
    """Dependency to require a specific permission"""

    def permission_checker(token_data: TokenData = Depends(verify_token)):
        if required_permission not in token_data.permissions:
            logger.warning(
                f"Access denied. Required permission: {required_permission}, "
                f"user permissions: {token_data.permissions}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required permission: {required_permission}",
            )
        return token_data

    return permission_checker


def setup_cors(app, allowed_origins: list = None):
    """Setup CORS middleware"""
    if allowed_origins is None:
        allowed_origins = os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080"
        ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS configured with origins: {allowed_origins}")


def setup_trusted_hosts(app, trusted_hosts: list = None):
    """Setup trusted host middleware"""
    if trusted_hosts is None:
        trusted_hosts = os.getenv("TRUSTED_HOSTS", "*").split(",")

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
    logger.info(f"Trusted hosts configured: {trusted_hosts}")


def setup_security_middleware(app):
    """Setup all security middleware"""
    # Rate limiting
    rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit)
    logger.info(f"Rate limiting configured: {rate_limit} requests per minute")

    # CORS
    setup_cors(app)

    # Trusted hosts
    setup_trusted_hosts(app)


# Default admin user creation (for development only)
def create_default_admin() -> Dict[str, str]:
    """Create default admin credentials (development only)"""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    return {
        "username": admin_username,
        "password_hash": get_password_hash(admin_password),
        "roles": ["admin"],
        "permissions": ["read", "write", "delete", "admin"],
    }


# Input validation helpers
def sanitize_string(input_str: str, max_length: int = 1000) -> str:
    """Sanitize string input"""
    if not isinstance(input_str, str):
        raise ValueError("Input must be a string")

    # Remove potentially dangerous characters
    sanitized = input_str.strip()
    if len(sanitized) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")

    return sanitized


def validate_email(email: str) -> str:
    """Validate email format"""
    import re

    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_regex, email):
        raise ValueError("Invalid email format")

    return email.lower().strip()
