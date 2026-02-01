"""
Authentication middleware for DealFlow AI Copilot.

Supports two authentication methods:
1. JWT Bearer tokens (for user sessions)
2. API Key headers (for programmatic access)
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings
from app.utils.logger import logger

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer scheme
bearer_scheme = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: str
    email: str
    role: str = "analyst"
    exp: Optional[datetime] = None


class AuthUser(BaseModel):
    """Authenticated user context."""
    user_id: str
    email: str
    role: str
    auth_method: str  # "jwt" or "api_key"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenData:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return TokenData(
            user_id=payload.get("sub", ""),
            email=payload.get("email", ""),
            role=payload.get("role", "analyst"),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_api_key(api_key: str) -> bool:
    """Validate an API key against configured keys."""
    valid_keys = settings.api_key_list
    if not valid_keys:
        return True  # No API keys configured = allow all (dev mode)
    return api_key in valid_keys


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[AuthUser]:
    """
    Extract and validate the current user from request.

    Checks in order:
    1. Bearer JWT token
    2. X-API-Key header
    3. Returns None if no auth present (for optional auth routes)
    """
    # Check Bearer token
    if credentials and credentials.credentials:
        token_data = decode_access_token(credentials.credentials)
        return AuthUser(
            user_id=token_data.user_id,
            email=token_data.email,
            role=token_data.role,
            auth_method="jwt",
        )

    # Check API Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        if validate_api_key(api_key):
            return AuthUser(
                user_id="api_key_user",
                email="api@dealflow.ai",
                role="analyst",
                auth_method="api_key",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return None


async def require_auth(
    user: Optional[AuthUser] = Depends(get_current_user),
) -> AuthUser:
    """
    Dependency that requires authentication.

    Usage:
        @router.get("/protected")
        async def protected(user: AuthUser = Depends(require_auth)):
            ...
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token or X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class AuthMiddleware:
    """
    ASGI middleware for authentication logging.

    Logs authentication attempts and provides request context.
    Does NOT block requests — use the require_auth dependency for that.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            api_key = headers.get(b"x-api-key", b"").decode()

            if auth_header:
                logger.debug(f"Request with Bearer auth: {scope['path']}")
            elif api_key:
                logger.debug(f"Request with API key: {scope['path']}")

        await self.app(scope, receive, send)
