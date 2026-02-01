"""
Tests for authentication endpoints.

Endpoints under test:
- POST /api/v1/auth/register  -> Register a new user
- POST /api/v1/auth/login     -> Login and get JWT token
- GET  /api/v1/auth/me        -> Get current user profile
- POST /api/v1/auth/api-key   -> Generate an API key

Run with: pytest tests/test_auth.py -v
"""

from typing import Any

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register_user(
    client: AsyncClient,
    email: str = "auth-test@dealflow.ai",
    password: str = "StrongPass123!",
    full_name: str = "Auth Tester",
    organization: str = "Test Fund",
) -> dict[str, Any]:
    """Register a user and return the response body."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "organization": organization,
        },
    )
    return response.json()


async def _login_user(
    client: AsyncClient,
    email: str = "auth-test@dealflow.ai",
    password: str = "StrongPass123!",
) -> dict[str, Any]:
    """Login a user and return the response body."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()


def _auth_headers(token: str) -> dict[str, str]:
    """Build an Authorization header from a JWT token."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register
# ---------------------------------------------------------------------------

class TestRegister:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_returns_200(self, async_client: AsyncClient) -> None:
        """Registering a new user should return HTTP 200."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "reg-new@dealflow.ai",
                "password": "ValidPass99!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_register_returns_token(self, async_client: AsyncClient) -> None:
        """Registration should return an access token."""
        data = await _register_user(
            async_client, email="reg-token@dealflow.ai"
        )
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_register_returns_user_info(self, async_client: AsyncClient) -> None:
        """Registration should return user profile data."""
        data = await _register_user(
            async_client, email="reg-info@dealflow.ai", full_name="Info User"
        )
        assert "user" in data
        assert data["user"]["email"] == "reg-info@dealflow.ai"
        assert data["user"]["full_name"] == "Info User"
        assert data["user"]["role"] == "analyst"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_client: AsyncClient) -> None:
        """Registering with an existing email should return 409."""
        await _register_user(async_client, email="reg-dup@dealflow.ai")

        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "reg-dup@dealflow.ai", "password": "AnotherPass1!"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password(self, async_client: AsyncClient) -> None:
        """Registering with a password shorter than 8 chars should return 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "reg-short@dealflow.ai", "password": "short"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_email(self, async_client: AsyncClient) -> None:
        """Registering without an email should return 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"password": "ValidPass99!"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_expires_in(self, async_client: AsyncClient) -> None:
        """Registration response should include expires_in."""
        data = await _register_user(
            async_client, email="reg-exp@dealflow.ai"
        )
        assert "expires_in" in data
        assert data["expires_in"] > 0


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_login_returns_200(self, async_client: AsyncClient) -> None:
        """Login with valid credentials should return 200."""
        await _register_user(async_client, email="login-ok@dealflow.ai")
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login-ok@dealflow.ai", "password": "StrongPass123!"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_login_returns_token(self, async_client: AsyncClient) -> None:
        """Login should return a valid JWT access token."""
        await _register_user(async_client, email="login-token@dealflow.ai")
        data = await _login_user(async_client, email="login-token@dealflow.ai")
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_returns_user_info(self, async_client: AsyncClient) -> None:
        """Login should return user profile data."""
        await _register_user(
            async_client, email="login-info@dealflow.ai", full_name="Login User"
        )
        data = await _login_user(async_client, email="login-info@dealflow.ai")
        assert "user" in data
        assert data["user"]["email"] == "login-info@dealflow.ai"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client: AsyncClient) -> None:
        """Login with wrong password should return 401."""
        await _register_user(async_client, email="login-wrong@dealflow.ai")
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login-wrong@dealflow.ai", "password": "WrongPassword!"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client: AsyncClient) -> None:
        """Login with a nonexistent email should return 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@dealflow.ai", "password": "NoUser123!"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, async_client: AsyncClient) -> None:
        """Login with missing fields should return 422."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "incomplete@dealflow.ai"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------

class TestGetProfile:
    """Tests for getting the current user's profile."""

    @pytest.mark.asyncio
    async def test_me_with_valid_token(self, async_client: AsyncClient) -> None:
        """GET /api/v1/auth/me with a valid token should return 200."""
        reg_data = await _register_user(async_client, email="me-ok@dealflow.ai")
        token = reg_data["access_token"]

        response = await async_client.get(
            "/api/v1/auth/me", headers=_auth_headers(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_me_returns_user_data(self, async_client: AsyncClient) -> None:
        """GET /api/v1/auth/me should return user profile fields."""
        reg_data = await _register_user(async_client, email="me-data@dealflow.ai")
        token = reg_data["access_token"]

        response = await async_client.get(
            "/api/v1/auth/me", headers=_auth_headers(token)
        )
        data = response.json()
        assert "user_id" in data
        assert data["email"] == "me-data@dealflow.ai"
        assert data["role"] == "analyst"
        assert data["auth_method"] == "jwt"

    @pytest.mark.asyncio
    async def test_me_without_token(self, async_client: AsyncClient) -> None:
        """GET /api/v1/auth/me without a token should return 401."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_token(self, async_client: AsyncClient) -> None:
        """GET /api/v1/auth/me with an invalid token should return 401."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=_auth_headers("invalid.token.here"),
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/auth/api-key
# ---------------------------------------------------------------------------

class TestGenerateAPIKey:
    """Tests for API key generation."""

    @pytest.mark.asyncio
    async def test_generate_api_key_returns_200(self, async_client: AsyncClient) -> None:
        """Generating an API key with valid auth should return 200."""
        reg_data = await _register_user(async_client, email="apikey-ok@dealflow.ai")
        token = reg_data["access_token"]

        response = await async_client.post(
            "/api/v1/auth/api-key", headers=_auth_headers(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_api_key_format(self, async_client: AsyncClient) -> None:
        """Generated API key should start with 'df_' prefix."""
        reg_data = await _register_user(async_client, email="apikey-fmt@dealflow.ai")
        token = reg_data["access_token"]

        response = await async_client.post(
            "/api/v1/auth/api-key", headers=_auth_headers(token)
        )
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("df_")

    @pytest.mark.asyncio
    async def test_generate_api_key_includes_message(
        self, async_client: AsyncClient
    ) -> None:
        """API key response should include a storage reminder message."""
        reg_data = await _register_user(async_client, email="apikey-msg@dealflow.ai")
        token = reg_data["access_token"]

        response = await async_client.post(
            "/api/v1/auth/api-key", headers=_auth_headers(token)
        )
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_generate_api_key_without_auth(self, async_client: AsyncClient) -> None:
        """Generating an API key without authentication should return 401."""
        response = await async_client.post("/api/v1/auth/api-key")
        assert response.status_code == 401
