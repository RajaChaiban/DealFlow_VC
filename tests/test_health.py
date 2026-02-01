"""
Tests for health check endpoints.

Endpoints under test:
- GET /health        -> Overall health status
- GET /health/ready  -> Readiness check (ready to accept requests)
- GET /health/live   -> Liveness check (process is alive)

Run with: pytest tests/test_health.py -v
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealthCheck:
    """Tests for the main health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, async_client: AsyncClient) -> None:
        """GET /health should return HTTP 200."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_contains_status(self, async_client: AsyncClient) -> None:
        """GET /health response must include a 'status' field set to 'healthy'."""
        response = await async_client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_contains_version(self, async_client: AsyncClient) -> None:
        """GET /health response must include a 'version' field."""
        response = await async_client.get("/health")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    @pytest.mark.asyncio
    async def test_health_contains_timestamp(self, async_client: AsyncClient) -> None:
        """GET /health response must include an ISO-format 'timestamp' field."""
        response = await async_client.get("/health")
        data = response.json()
        assert "timestamp" in data
        # Basic ISO 8601 check -- contains 'T' separator
        assert "T" in data["timestamp"]

    @pytest.mark.asyncio
    async def test_health_contains_service_name(self, async_client: AsyncClient) -> None:
        """GET /health response must identify the service."""
        response = await async_client.get("/health")
        data = response.json()
        assert "service" in data
        assert data["service"] == "dealflow-ai-copilot"

    @pytest.mark.asyncio
    async def test_health_response_content_type(self, async_client: AsyncClient) -> None:
        """GET /health must return application/json."""
        response = await async_client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# GET /health/ready
# ---------------------------------------------------------------------------

class TestReadinessCheck:
    """Tests for the readiness probe endpoint."""

    @pytest.mark.asyncio
    async def test_ready_returns_200(self, async_client: AsyncClient) -> None:
        """GET /health/ready should return HTTP 200."""
        response = await async_client.get("/health/ready")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ready_returns_true(self, async_client: AsyncClient) -> None:
        """GET /health/ready response 'ready' field must be True."""
        response = await async_client.get("/health/ready")
        data = response.json()
        assert "ready" in data
        assert data["ready"] is True

    @pytest.mark.asyncio
    async def test_ready_contains_timestamp(self, async_client: AsyncClient) -> None:
        """GET /health/ready response must include a timestamp."""
        response = await async_client.get("/health/ready")
        data = response.json()
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# GET /health/live
# ---------------------------------------------------------------------------

class TestLivenessCheck:
    """Tests for the liveness probe endpoint."""

    @pytest.mark.asyncio
    async def test_live_returns_200(self, async_client: AsyncClient) -> None:
        """GET /health/live should return HTTP 200."""
        response = await async_client.get("/health/live")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_live_returns_alive(self, async_client: AsyncClient) -> None:
        """GET /health/live response 'alive' field must be True."""
        response = await async_client.get("/health/live")
        data = response.json()
        assert "alive" in data
        assert data["alive"] is True

    @pytest.mark.asyncio
    async def test_live_contains_timestamp(self, async_client: AsyncClient) -> None:
        """GET /health/live response must include a timestamp."""
        response = await async_client.get("/health/live")
        data = response.json()
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------------------------

class TestRootEndpoint:
    """Tests for the root '/' endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_200(self, async_client: AsyncClient) -> None:
        """GET / should return HTTP 200."""
        response = await async_client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_contains_name(self, async_client: AsyncClient) -> None:
        """GET / should return the app name."""
        response = await async_client.get("/")
        data = response.json()
        assert "name" in data

    @pytest.mark.asyncio
    async def test_root_contains_docs_links(self, async_client: AsyncClient) -> None:
        """GET / should include documentation URLs."""
        response = await async_client.get("/")
        data = response.json()
        assert "documentation" in data
        docs = data["documentation"]
        assert "swagger" in docs
        assert "redoc" in docs
