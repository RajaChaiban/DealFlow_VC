"""
Tests for deal analysis endpoints.

Endpoints under test:
- POST /api/v1/deals/upload          -> Upload a pitch deck PDF
- POST /api/v1/deals/analyze/sync    -> Synchronous analysis
- GET  /api/v1/deals                 -> List all analyses
- GET  /api/v1/deals/{id}/status     -> Get analysis status (404 for unknown)

Run with: pytest tests/test_deals.py -v
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# POST /api/v1/deals/upload
# ---------------------------------------------------------------------------

class TestUploadPitchDeck:
    """Tests for pitch deck upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_valid_pdf(self, async_client: AsyncClient) -> None:
        """Uploading a valid PDF file should return 200 with file metadata."""
        # Minimal valid-looking PDF bytes
        pdf_bytes = b"%PDF-1.4 fake pdf content for testing"

        with patch("app.api.deals.get_document_service") as mock_svc:
            mock_service = MagicMock()
            mock_service.save_upload = AsyncMock(
                return_value=MagicMock(
                    file_id="test-file-123",
                    filename="pitch.pdf",
                    file_path="/data/uploads/pitch.pdf",
                    file_size_bytes=len(pdf_bytes),
                    mime_type="application/pdf",
                    uploaded_at="2024-01-15T10:00:00",
                )
            )
            mock_svc.return_value = mock_service

            response = await async_client.post(
                "/api/v1/deals/upload",
                files={"file": ("pitch.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "test-file-123"
        assert data["filename"] == "pitch.pdf"

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, async_client: AsyncClient) -> None:
        """Uploading a non-PDF file should return 400."""
        txt_bytes = b"This is a plain text file, not a PDF."

        response = await async_client.post(
            "/api/v1/deals/upload",
            files={"file": ("document.txt", io.BytesIO(txt_bytes), "text/plain")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "PDF" in data["detail"] or "Invalid" in data["detail"]

    @pytest.mark.asyncio
    async def test_upload_no_file(self, async_client: AsyncClient) -> None:
        """Uploading with no file should return 422 (validation error)."""
        response = await async_client.post("/api/v1/deals/upload")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_image_rejected(self, async_client: AsyncClient) -> None:
        """Uploading an image file should return 400."""
        png_bytes = b"\x89PNG\r\n\x1a\n fake image"

        response = await async_client.post(
            "/api/v1/deals/upload",
            files={"file": ("slide.png", io.BytesIO(png_bytes), "image/png")},
        )

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/v1/deals/analyze/sync
# ---------------------------------------------------------------------------

class TestAnalyzeSync:
    """Tests for synchronous deal analysis endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_sync_invalid_content_type(self, async_client: AsyncClient) -> None:
        """Sync analysis with a non-PDF should return 400."""
        response = await async_client.post(
            "/api/v1/deals/analyze/sync",
            files={"file": ("doc.txt", io.BytesIO(b"not a pdf"), "text/plain")},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_analyze_sync_returns_analysis_response(
        self, async_client: AsyncClient
    ) -> None:
        """Sync analysis with a valid PDF should return an AnalysisResponse."""
        pdf_bytes = b"%PDF-1.4 test pitch deck content"

        with (
            patch("app.api.deals.get_document_service") as mock_svc,
            patch("app.api.deals.OrchestratorAgent") as mock_orch_cls,
        ):
            # Mock document service
            mock_service = MagicMock()
            mock_service.process_pdf_bytes = AsyncMock(
                return_value=(
                    [MagicMock()],  # images
                    "Extracted text from pitch deck",
                )
            )
            mock_svc.return_value = mock_service

            # Mock orchestrator -- return a mock ICMemo
            mock_orch = MagicMock()
            mock_memo = MagicMock()
            mock_memo.model_dump.return_value = {"company_name": "TestCo"}
            mock_orch.analyze = AsyncMock(return_value=mock_memo)
            mock_orch_cls.return_value = mock_orch

            response = await async_client.post(
                "/api/v1/deals/analyze/sync",
                files={"file": ("pitch.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] in ("completed", "failed")

    @pytest.mark.asyncio
    async def test_analyze_sync_no_file(self, async_client: AsyncClient) -> None:
        """Sync analysis without a file should return 422."""
        response = await async_client.post("/api/v1/deals/analyze/sync")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/deals
# ---------------------------------------------------------------------------

class TestListAnalyses:
    """Tests for listing analyses endpoint."""

    @pytest.mark.asyncio
    async def test_list_analyses_returns_200(self, async_client: AsyncClient) -> None:
        """GET /api/v1/deals should return HTTP 200."""
        response = await async_client.get("/api/v1/deals")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_analyses_structure(self, async_client: AsyncClient) -> None:
        """GET /api/v1/deals response should include 'total' and 'analyses' fields."""
        response = await async_client.get("/api/v1/deals")
        data = response.json()
        assert "total" in data
        assert "analyses" in data
        assert isinstance(data["analyses"], list)

    @pytest.mark.asyncio
    async def test_list_analyses_with_status_filter(self, async_client: AsyncClient) -> None:
        """GET /api/v1/deals?status=completed should accept the filter."""
        response = await async_client.get("/api/v1/deals?status=completed")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/deals/{id}/status
# ---------------------------------------------------------------------------

class TestGetAnalysisStatus:
    """Tests for individual analysis status endpoint."""

    @pytest.mark.asyncio
    async def test_status_nonexistent_returns_404(self, async_client: AsyncClient) -> None:
        """GET /api/v1/deals/{id}/status for a nonexistent ID should return 404."""
        response = await async_client.get("/api/v1/deals/nonexistent-id-999/status")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_status_404_contains_detail(self, async_client: AsyncClient) -> None:
        """404 response should contain a descriptive 'detail' field."""
        response = await async_client.get("/api/v1/deals/bad-id/status")
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_result_nonexistent_returns_404(self, async_client: AsyncClient) -> None:
        """GET /api/v1/deals/{id}/result for a nonexistent ID should return 404."""
        response = await async_client.get("/api/v1/deals/missing-id/result")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/deals/{id}
# ---------------------------------------------------------------------------

class TestDeleteAnalysis:
    """Tests for deleting an analysis."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, async_client: AsyncClient) -> None:
        """DELETE /api/v1/deals/{id} for nonexistent ID should return 404."""
        response = await async_client.delete("/api/v1/deals/no-such-id")
        assert response.status_code == 404
