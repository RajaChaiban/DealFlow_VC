"""
Tests for conversational deal analysis (chat) endpoints.

Endpoints under test:
- POST /api/v1/chat/                  -> Send a chat message
- GET  /api/v1/chat/{session_id}/history -> Get chat history
- GET  /api/v1/chat/sessions          -> List active sessions
- DELETE /api/v1/chat/{session_id}    -> Delete a chat session

Run with: pytest tests/test_chat.py -v
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _send_chat_message(
    client: AsyncClient,
    message: str = "What is the revenue?",
    session_id: str | None = None,
    analysis_id: str | None = None,
) -> dict[str, Any]:
    """Helper to send a chat message and return the response body."""
    payload: dict[str, Any] = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    if analysis_id:
        payload["analysis_id"] = analysis_id

    with patch("app.api.chat.get_gemini_client") as mock_get:
        mock_client = MagicMock()
        mock_client.generate_structured = AsyncMock(
            return_value={
                "response": "The company has $3.2M ARR.",
                "sources": ["financials.arr"],
                "suggested_questions": [
                    "What is the growth rate?",
                    "What about unit economics?",
                ],
            }
        )
        mock_get.return_value = mock_client

        response = await client.post("/api/v1/chat/", json=payload)

    return response.json()


# ---------------------------------------------------------------------------
# POST /api/v1/chat/
# ---------------------------------------------------------------------------

class TestChatMessage:
    """Tests for sending chat messages."""

    @pytest.mark.asyncio
    async def test_chat_returns_200(self, async_client: AsyncClient) -> None:
        """POST /api/v1/chat/ should return HTTP 200."""
        with patch("app.api.chat.get_gemini_client") as mock_get:
            mock_client = MagicMock()
            mock_client.generate_structured = AsyncMock(
                return_value={
                    "response": "Mock response.",
                    "sources": [],
                    "suggested_questions": [],
                }
            )
            mock_get.return_value = mock_client

            response = await async_client.post(
                "/api/v1/chat/",
                json={"message": "Hello, tell me about this deal."},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_response_structure(self, async_client: AsyncClient) -> None:
        """Chat response should contain required fields."""
        data = await _send_chat_message(async_client)

        assert "session_id" in data
        assert "response" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_chat_returns_session_id(self, async_client: AsyncClient) -> None:
        """Chat should generate a session_id when none is provided."""
        data = await _send_chat_message(async_client, message="First message")
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    @pytest.mark.asyncio
    async def test_chat_reuses_session_id(self, async_client: AsyncClient) -> None:
        """Providing a session_id should maintain conversation continuity."""
        first = await _send_chat_message(async_client, message="First question")
        sid = first["session_id"]

        second = await _send_chat_message(
            async_client, message="Follow-up question", session_id=sid
        )
        assert second["session_id"] == sid

    @pytest.mark.asyncio
    async def test_chat_with_analysis_id(self, async_client: AsyncClient) -> None:
        """Chat should accept an analysis_id for deal context."""
        data = await _send_chat_message(
            async_client,
            message="What are the risks?",
            analysis_id="deal-123",
        )
        assert data.get("analysis_id") == "deal-123"

    @pytest.mark.asyncio
    async def test_chat_suggested_questions(self, async_client: AsyncClient) -> None:
        """Chat response should include suggested follow-up questions."""
        data = await _send_chat_message(async_client)
        assert "suggested_questions" in data
        assert isinstance(data["suggested_questions"], list)

    @pytest.mark.asyncio
    async def test_chat_sources(self, async_client: AsyncClient) -> None:
        """Chat response should include source references."""
        data = await _send_chat_message(async_client)
        assert "sources" in data
        assert isinstance(data["sources"], list)

    @pytest.mark.asyncio
    async def test_chat_empty_message_fails(self, async_client: AsyncClient) -> None:
        """Sending an empty message body should return 422."""
        response = await async_client.post("/api/v1/chat/", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/chat/{session_id}/history
# ---------------------------------------------------------------------------

class TestChatHistory:
    """Tests for retrieving chat history."""

    @pytest.mark.asyncio
    async def test_history_returns_200(self, async_client: AsyncClient) -> None:
        """GET /api/v1/chat/{id}/history should return 200 for an existing session."""
        data = await _send_chat_message(async_client, message="History test")
        sid = data["session_id"]

        response = await async_client.get(f"/api/v1/chat/{sid}/history")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_history_contains_messages(self, async_client: AsyncClient) -> None:
        """Chat history should contain the exchanged messages."""
        data = await _send_chat_message(async_client, message="Track this message")
        sid = data["session_id"]

        response = await async_client.get(f"/api/v1/chat/{sid}/history")
        history = response.json()

        assert "messages" in history
        assert history["message_count"] >= 2  # user + assistant
        # Check that the user message is in history
        user_messages = [m for m in history["messages"] if m["role"] == "user"]
        assert any("Track this message" in m["content"] for m in user_messages)

    @pytest.mark.asyncio
    async def test_history_nonexistent_session(self, async_client: AsyncClient) -> None:
        """GET /api/v1/chat/{id}/history for a nonexistent session should return 404."""
        response = await async_client.get("/api/v1/chat/no-such-session/history")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_history_includes_session_metadata(
        self, async_client: AsyncClient
    ) -> None:
        """History response should include session metadata."""
        data = await _send_chat_message(async_client, message="Metadata test")
        sid = data["session_id"]

        response = await async_client.get(f"/api/v1/chat/{sid}/history")
        history = response.json()

        assert "session_id" in history
        assert "created_at" in history
        assert "message_count" in history


# ---------------------------------------------------------------------------
# GET /api/v1/chat/sessions
# ---------------------------------------------------------------------------

class TestListSessions:
    """Tests for listing active chat sessions."""

    @pytest.mark.asyncio
    async def test_list_sessions_returns_200(self, async_client: AsyncClient) -> None:
        """GET /api/v1/chat/sessions should return HTTP 200."""
        response = await async_client.get("/api/v1/chat/sessions")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_sessions_structure(self, async_client: AsyncClient) -> None:
        """Sessions list should include 'total' and 'sessions' fields."""
        response = await async_client.get("/api/v1/chat/sessions")
        data = response.json()
        assert "total" in data
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    @pytest.mark.asyncio
    async def test_list_sessions_after_chat(self, async_client: AsyncClient) -> None:
        """After sending a message, the session should appear in the list."""
        await _send_chat_message(async_client, message="Session list test")

        response = await async_client.get("/api/v1/chat/sessions")
        data = response.json()
        assert data["total"] >= 1


# ---------------------------------------------------------------------------
# DELETE /api/v1/chat/{session_id}
# ---------------------------------------------------------------------------

class TestDeleteSession:
    """Tests for deleting chat sessions."""

    @pytest.mark.asyncio
    async def test_delete_existing_session(self, async_client: AsyncClient) -> None:
        """Deleting an existing session should succeed."""
        data = await _send_chat_message(async_client, message="Delete me")
        sid = data["session_id"]

        response = await async_client.delete(f"/api/v1/chat/{sid}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower() or "Session" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, async_client: AsyncClient) -> None:
        """Deleting a nonexistent session should return 404."""
        response = await async_client.delete("/api/v1/chat/ghost-session")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_then_history_404(self, async_client: AsyncClient) -> None:
        """After deleting a session, its history should return 404."""
        data = await _send_chat_message(async_client, message="Delete and check")
        sid = data["session_id"]

        await async_client.delete(f"/api/v1/chat/{sid}")

        response = await async_client.get(f"/api/v1/chat/{sid}/history")
        assert response.status_code == 404
