"""
Tests for deal pipeline (Kanban board) endpoints.

Endpoints under test:
- POST /api/v1/pipeline/             -> Add deal to pipeline
- GET  /api/v1/pipeline/             -> Get pipeline board (Kanban)
- PUT  /api/v1/pipeline/{id}/stage   -> Transition deal to new stage
- GET  /api/v1/pipeline/stats        -> Pipeline statistics

Run with: pytest tests/test_pipeline.py -v
"""

from typing import Any

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _add_pipeline_entry(
    client: AsyncClient,
    analysis_id: str = "deal-001",
    company_name: str = "TestCo",
    stage: str = "new",
    priority: str = "medium",
) -> dict[str, Any]:
    """Helper to add a deal to the pipeline and return the response body."""
    response = await client.post(
        "/api/v1/pipeline/",
        json={
            "analysis_id": analysis_id,
            "company_name": company_name,
            "stage": stage,
            "priority": priority,
            "tags": ["saas", "ai"],
            "notes": "Interesting deal",
        },
    )
    return response.json()


# ---------------------------------------------------------------------------
# POST /api/v1/pipeline/
# ---------------------------------------------------------------------------

class TestAddToPipeline:
    """Tests for adding deals to the pipeline."""

    @pytest.mark.asyncio
    async def test_add_deal_returns_200(self, async_client: AsyncClient) -> None:
        """Adding a deal to the pipeline should succeed."""
        response = await async_client.post(
            "/api/v1/pipeline/",
            json={
                "analysis_id": "pipe-add-001",
                "company_name": "NewDealCo",
                "stage": "new",
                "priority": "high",
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_deal_response_structure(self, async_client: AsyncClient) -> None:
        """Response should contain 'message', 'id', and 'entry'."""
        response = await async_client.post(
            "/api/v1/pipeline/",
            json={
                "analysis_id": "pipe-add-002",
                "company_name": "StructureCo",
                "stage": "screening",
            },
        )
        data = response.json()
        assert "message" in data
        assert "id" in data
        assert "entry" in data
        assert data["entry"]["company_name"] == "StructureCo"
        assert data["entry"]["stage"] == "screening"

    @pytest.mark.asyncio
    async def test_add_deal_invalid_stage(self, async_client: AsyncClient) -> None:
        """Adding a deal with an invalid stage should return 400."""
        response = await async_client.post(
            "/api/v1/pipeline/",
            json={
                "analysis_id": "pipe-add-003",
                "company_name": "BadStageCo",
                "stage": "invalid_stage",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_add_deal_has_stage_history(self, async_client: AsyncClient) -> None:
        """Newly added deal should have initial stage history."""
        data = await _add_pipeline_entry(
            async_client, analysis_id="pipe-add-004", company_name="HistoryCo"
        )
        entry = data["entry"]
        assert "stage_history" in entry
        assert len(entry["stage_history"]) == 1
        assert entry["stage_history"][0]["stage"] == "new"

    @pytest.mark.asyncio
    async def test_add_deal_default_priority(self, async_client: AsyncClient) -> None:
        """Default priority should be 'medium'."""
        response = await async_client.post(
            "/api/v1/pipeline/",
            json={
                "analysis_id": "pipe-add-005",
                "company_name": "DefaultPriorityCo",
            },
        )
        data = response.json()
        assert data["entry"]["priority"] == "medium"


# ---------------------------------------------------------------------------
# GET /api/v1/pipeline/
# ---------------------------------------------------------------------------

class TestGetPipelineBoard:
    """Tests for the pipeline board (Kanban view)."""

    @pytest.mark.asyncio
    async def test_board_returns_200(self, async_client: AsyncClient) -> None:
        """GET /api/v1/pipeline/ should return HTTP 200."""
        response = await async_client.get("/api/v1/pipeline/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_board_has_all_stages(self, async_client: AsyncClient) -> None:
        """Board should contain all valid pipeline stages."""
        response = await async_client.get("/api/v1/pipeline/")
        data = response.json()
        assert "stages" in data
        expected_stages = [
            "new", "screening", "diligence", "ic_review",
            "term_sheet", "closed_won", "closed_lost", "passed",
        ]
        assert data["stages"] == expected_stages

    @pytest.mark.asyncio
    async def test_board_has_counts(self, async_client: AsyncClient) -> None:
        """Board should include deal counts by stage."""
        response = await async_client.get("/api/v1/pipeline/")
        data = response.json()
        assert "counts" in data
        assert "total_deals" in data
        assert "active_deals" in data

    @pytest.mark.asyncio
    async def test_board_reflects_added_deal(self, async_client: AsyncClient) -> None:
        """Adding a deal should make it visible on the board."""
        await _add_pipeline_entry(
            async_client, analysis_id="pipe-board-001", company_name="VisibleCo"
        )
        response = await async_client.get("/api/v1/pipeline/")
        data = response.json()
        assert data["total_deals"] >= 1


# ---------------------------------------------------------------------------
# PUT /api/v1/pipeline/{id}/stage
# ---------------------------------------------------------------------------

class TestStageTransition:
    """Tests for moving deals between pipeline stages."""

    @pytest.mark.asyncio
    async def test_transition_stage(self, async_client: AsyncClient) -> None:
        """Moving a deal to a new stage should succeed."""
        # First add a deal
        await _add_pipeline_entry(
            async_client, analysis_id="pipe-trans-001", company_name="TransitionCo"
        )

        # Move it from new -> screening
        response = await async_client.put(
            "/api/v1/pipeline/pipe-trans-001/stage",
            json={"new_stage": "screening", "notes": "Passed initial filter"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Moved from" in data["message"]
        assert data["entry"]["stage"] == "screening"

    @pytest.mark.asyncio
    async def test_transition_updates_history(self, async_client: AsyncClient) -> None:
        """Stage transition should update the stage history."""
        await _add_pipeline_entry(
            async_client, analysis_id="pipe-trans-002", company_name="HistoryTransCo"
        )
        await async_client.put(
            "/api/v1/pipeline/pipe-trans-002/stage",
            json={"new_stage": "diligence"},
        )
        response = await async_client.put(
            "/api/v1/pipeline/pipe-trans-002/stage",
            json={"new_stage": "ic_review"},
        )
        data = response.json()
        assert len(data["entry"]["stage_history"]) == 3  # new -> diligence -> ic_review

    @pytest.mark.asyncio
    async def test_transition_invalid_stage(self, async_client: AsyncClient) -> None:
        """Transitioning to an invalid stage should return 400."""
        await _add_pipeline_entry(
            async_client, analysis_id="pipe-trans-003", company_name="BadTransCo"
        )
        response = await async_client.put(
            "/api/v1/pipeline/pipe-trans-003/stage",
            json={"new_stage": "nonexistent_stage"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_transition_nonexistent_entry(self, async_client: AsyncClient) -> None:
        """Transitioning a nonexistent entry should return 404."""
        response = await async_client.put(
            "/api/v1/pipeline/does-not-exist/stage",
            json={"new_stage": "screening"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/pipeline/stats
# ---------------------------------------------------------------------------

class TestPipelineStats:
    """Tests for pipeline statistics endpoint."""

    @pytest.mark.asyncio
    async def test_stats_returns_200(self, async_client: AsyncClient) -> None:
        """GET /api/v1/pipeline/stats should return HTTP 200."""
        response = await async_client.get("/api/v1/pipeline/stats")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stats_structure(self, async_client: AsyncClient) -> None:
        """Stats response should have expected fields."""
        response = await async_client.get("/api/v1/pipeline/stats")
        data = response.json()
        assert "total_deals" in data
        assert "active_deals" in data
        assert "stage_distribution" in data
        assert "priority_distribution" in data
        assert "conversion_rate" in data

    @pytest.mark.asyncio
    async def test_stats_stage_distribution(self, async_client: AsyncClient) -> None:
        """Stage distribution should contain all valid stages."""
        response = await async_client.get("/api/v1/pipeline/stats")
        data = response.json()
        dist = data["stage_distribution"]
        for stage in ["new", "screening", "diligence", "ic_review", "term_sheet"]:
            assert stage in dist

    @pytest.mark.asyncio
    async def test_stats_priority_distribution(self, async_client: AsyncClient) -> None:
        """Priority distribution should contain all priority levels."""
        response = await async_client.get("/api/v1/pipeline/stats")
        data = response.json()
        dist = data["priority_distribution"]
        for priority in ["low", "medium", "high", "urgent"]:
            assert priority in dist


# ---------------------------------------------------------------------------
# DELETE /api/v1/pipeline/{id}
# ---------------------------------------------------------------------------

class TestDeletePipelineEntry:
    """Tests for removing deals from the pipeline."""

    @pytest.mark.asyncio
    async def test_delete_existing_entry(self, async_client: AsyncClient) -> None:
        """Deleting an existing entry should succeed."""
        await _add_pipeline_entry(
            async_client, analysis_id="pipe-del-001", company_name="DeleteMe"
        )
        response = await async_client.delete("/api/v1/pipeline/pipe-del-001")
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entry(self, async_client: AsyncClient) -> None:
        """Deleting a nonexistent entry should return 404."""
        response = await async_client.delete("/api/v1/pipeline/no-such-entry")
        assert response.status_code == 404
