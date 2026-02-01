"""
End-to-end integration tests for DealFlow AI Copilot.

Tests the full user journey:
  Register → Login → Upload/Analyze → Pipeline → Chat → Export → Analytics

All external services (Gemini, Redis) are mocked via conftest fixtures.
Uses an in-memory SQLite database for persistence.
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def register_and_login(client: AsyncClient) -> str:
    """Register a user and return the JWT access token."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "integration@dealflow.ai",
            "password": "IntegrationPass123!",
            "full_name": "Integration Tester",
            "organization": "Integration Fund",
        },
    )
    assert reg.status_code == 200, f"Registration failed: {reg.text}"
    return reg.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    """Build Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Full Integration Flow
# ---------------------------------------------------------------------------

class TestFullDealFlow:
    """
    End-to-end test: register → analyze → pipeline → chat → analytics.

    Each method is an independent step but they share the same async_client
    session (same in-memory DB) via pytest ordering.
    """

    @pytest.mark.asyncio
    async def test_01_register_and_get_profile(self, async_client: AsyncClient) -> None:
        """Register, login, and fetch profile."""
        token = await register_and_login(async_client)

        me = await async_client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert me.status_code == 200
        data = me.json()
        assert data["email"] == "integration@dealflow.ai"
        assert data["role"] == "analyst"

    @pytest.mark.asyncio
    async def test_02_login_existing_user(self, async_client: AsyncClient) -> None:
        """Register then login with credentials."""
        # Register first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "login-test@dealflow.ai",
                "password": "LoginPass123!",
                "full_name": "Login Tester",
            },
        )

        # Login
        login = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login-test@dealflow.ai", "password": "LoginPass123!"},
        )
        assert login.status_code == 200
        data = login.json()
        assert "access_token" in data
        assert data["user"]["email"] == "login-test@dealflow.ai"

    @pytest.mark.asyncio
    async def test_03_analyze_deal_sync(self, async_client: AsyncClient) -> None:
        """Upload a PDF and run synchronous analysis with mocked agents."""
        pdf_bytes = b"%PDF-1.4 test pitch deck content for integration test"

        with (
            patch("app.api.deals.get_document_service") as mock_svc,
            patch("app.api.deals.OrchestratorAgent") as mock_orch_cls,
        ):
            # Mock document service
            mock_service = MagicMock()
            mock_service.process_pdf_bytes = AsyncMock(
                return_value=([MagicMock()], "Extracted pitch deck text")
            )
            mock_svc.return_value = mock_service

            # Mock orchestrator with a result whose model_dump returns a dict
            mock_orch = MagicMock()
            mock_memo = MagicMock()
            mock_memo.model_dump.return_value = {
                "company_name": "IntegrationCo",
                "executive_summary": {"recommendation": "invest"},
                "extraction_result": {"company_name": "IntegrationCo"},
            }
            mock_orch.analyze = AsyncMock(return_value=mock_memo)
            mock_orch_cls.return_value = mock_orch

            response = await async_client.post(
                "/api/v1/deals/analyze/sync",
                files={"file": ("deck.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_04_list_deals_empty(self, async_client: AsyncClient) -> None:
        """List analyses (may be empty in a fresh test DB)."""
        response = await async_client.get("/api/v1/deals")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "analyses" in data
        assert isinstance(data["analyses"], list)

    @pytest.mark.asyncio
    async def test_05_pipeline_full_lifecycle(self, async_client: AsyncClient) -> None:
        """Add deal to pipeline → move through stages → verify board → delete."""
        # Add to pipeline
        add_resp = await async_client.post(
            "/api/v1/pipeline/",
            json={
                "analysis_id": "integ-001",
                "company_name": "IntegrationCo",
                "stage": "new",
                "priority": "high",
                "tags": ["AI", "SaaS"],
                "notes": "Integration test deal",
            },
        )
        assert add_resp.status_code == 200
        entry = add_resp.json()["entry"]
        assert entry["company_name"] == "IntegrationCo"
        assert entry["stage"] == "new"
        assert entry["priority"] == "high"

        # Move to screening
        stage_resp = await async_client.put(
            "/api/v1/pipeline/integ-001/stage",
            json={"new_stage": "screening", "notes": "Passed initial filter"},
        )
        assert stage_resp.status_code == 200
        assert stage_resp.json()["entry"]["stage"] == "screening"

        # Move to diligence
        stage_resp2 = await async_client.put(
            "/api/v1/pipeline/integ-001/stage",
            json={"new_stage": "diligence"},
        )
        assert stage_resp2.status_code == 200
        assert stage_resp2.json()["entry"]["stage"] == "diligence"

        # Check stage history has 3 entries (new → screening → diligence)
        history = stage_resp2.json()["entry"]["stage_history"]
        assert len(history) == 3

        # Get pipeline board
        board_resp = await async_client.get("/api/v1/pipeline/")
        assert board_resp.status_code == 200
        board = board_resp.json()
        assert "board" in board
        assert "stages" in board
        assert board["total_deals"] >= 1

        # Get pipeline stats
        stats_resp = await async_client.get("/api/v1/pipeline/stats")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert "total_deals" in stats
        assert "stage_distribution" in stats

        # Update metadata
        update_resp = await async_client.put(
            "/api/v1/pipeline/integ-001",
            json={"priority": "urgent", "assigned_to": "Jane Doe"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["entry"]["priority"] == "urgent"

        # Delete from pipeline
        del_resp = await async_client.delete("/api/v1/pipeline/integ-001")
        assert del_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_06_chat_with_ai(self, async_client: AsyncClient) -> None:
        """Send a chat message and verify the response structure."""
        with patch("app.api.chat.get_gemini_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.generate_structured = AsyncMock(
                return_value={
                    "response": "The company has strong fundamentals.",
                    "sources": ["Financial data"],
                    "suggested_questions": ["What about growth?"],
                }
            )
            mock_client_fn.return_value = mock_client

            chat_resp = await async_client.post(
                "/api/v1/chat/",
                json={"message": "What are the key strengths?"},
            )

        assert chat_resp.status_code == 200
        data = chat_resp.json()
        assert "session_id" in data
        assert "response" in data
        assert len(data["response"]) > 0
        assert "suggested_questions" in data

        session_id = data["session_id"]

        # List sessions
        sessions_resp = await async_client.get("/api/v1/chat/sessions")
        assert sessions_resp.status_code == 200
        sessions = sessions_resp.json()
        assert sessions["total"] >= 1

        # Get chat history
        history_resp = await async_client.get(f"/api/v1/chat/{session_id}/history")
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert history["message_count"] >= 2  # user + assistant

    @pytest.mark.asyncio
    async def test_07_analytics_endpoint(self, async_client: AsyncClient) -> None:
        """Verify portfolio analytics returns expected structure."""
        response = await async_client.get("/api/v1/analytics/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert "total_deals_analyzed" in data
        assert "score_distribution" in data
        assert "recommendation_breakdown" in data
        assert "pipeline" in data

    @pytest.mark.asyncio
    async def test_08_generate_api_key(self, async_client: AsyncClient) -> None:
        """Register → get token → generate API key."""
        token = await register_and_login(async_client)

        key_resp = await async_client.post(
            "/api/v1/auth/api-key",
            headers=auth_headers(token),
        )
        assert key_resp.status_code == 200
        data = key_resp.json()
        assert "api_key" in data
        assert data["api_key"].startswith("df_")


# ---------------------------------------------------------------------------
# Error / Edge-Case Tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for error handling and edge cases across endpoints."""

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_client: AsyncClient) -> None:
        """Registering with the same email twice returns 400."""
        user = {
            "email": "dup@dealflow.ai",
            "password": "DupPass123!",
            "full_name": "Dup User",
        }
        first = await async_client.post("/api/v1/auth/register", json=user)
        assert first.status_code == 200

        second = await async_client.post("/api/v1/auth/register", json=user)
        assert second.status_code == 409

    @pytest.mark.asyncio
    async def test_access_protected_route_without_token(
        self, async_client: AsyncClient
    ) -> None:
        """Hitting /me without a token returns 401."""
        resp = await async_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_pipeline_stage(self, async_client: AsyncClient) -> None:
        """Transitioning to an invalid pipeline stage returns 400."""
        await async_client.post(
            "/api/v1/pipeline/",
            json={"analysis_id": "edge-001", "company_name": "EdgeCo"},
        )
        resp = await async_client.put(
            "/api/v1/pipeline/edge-001/stage",
            json={"new_stage": "nonexistent_stage"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_analyze_wrong_file_type(self, async_client: AsyncClient) -> None:
        """Uploading a non-PDF returns 400."""
        resp = await async_client.post(
            "/api/v1/deals/analyze/sync",
            files={"file": ("report.txt", io.BytesIO(b"text content"), "text/plain")},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_pipeline_not_found(self, async_client: AsyncClient) -> None:
        """Updating a non-existent pipeline entry returns 404."""
        resp = await async_client.put(
            "/api/v1/pipeline/nonexistent/stage",
            json={"new_stage": "screening"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_history_not_found(self, async_client: AsyncClient) -> None:
        """Getting history for a non-existent session returns 404."""
        resp = await async_client.get("/api/v1/chat/nonexistent/history")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_health_and_liveness(self, async_client: AsyncClient) -> None:
        """Health, readiness, and liveness all return 200."""
        for path in ["/health", "/health/ready", "/health/live"]:
            resp = await async_client.get(path)
            assert resp.status_code == 200
