"""
Authentication API endpoints for DealFlow AI Copilot.

Handles user registration, login, token refresh, and API key management.
"""

import secrets
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import create_user, get_user_by_email, update_user_api_key
from app.database.session import get_db
from app.middleware.auth import (
    AuthUser,
    create_access_token,
    hash_password,
    require_auth,
    verify_password,
)
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    """User registration request."""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    full_name: Optional[str] = None
    organization: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict[str, Any]


class APIKeyResponse(BaseModel):
    """API key response."""
    api_key: str
    message: str


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register New User",
    description="Create a new user account and get an access token",
)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user."""
    # Check if user exists
    existing = await get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await create_user(
        db,
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        organization=req.organization,
    )

    token = create_access_token(data={
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })

    logger.info(f"User registered: {req.email}")

    return TokenResponse(
        access_token=token,
        expires_in=3600,
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "organization": user.organization,
            "role": user.role,
        },
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate and get an access token",
)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Login and get an access token."""
    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })

    logger.info(f"User logged in: {req.email}")

    return TokenResponse(
        access_token=token,
        expires_in=3600,
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "organization": user.organization,
            "role": user.role,
        },
    )


@router.post(
    "/api-key",
    response_model=APIKeyResponse,
    summary="Generate API Key",
    description="Generate a new API key for programmatic access",
)
async def generate_api_key(
    user: AuthUser = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """Generate a new API key for the authenticated user."""
    api_key = f"df_{secrets.token_urlsafe(32)}"

    await update_user_api_key(db, user.user_id, api_key)

    logger.info(f"API key generated for: {user.email}")

    return APIKeyResponse(
        api_key=api_key,
        message="Store this key securely. It won't be shown again.",
    )


@router.get(
    "/me",
    summary="Get Current User",
    description="Get the currently authenticated user's profile",
)
async def get_me(user: AuthUser = Depends(require_auth)) -> dict[str, Any]:
    """Get current user profile."""
    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "auth_method": user.auth_method,
    }
