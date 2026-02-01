"""
Deal Pipeline API for DealFlow AI Copilot.

Kanban-style deal tracking with stages:
new -> screening -> diligence -> ic_review -> term_sheet -> closed_won / closed_lost / passed
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import crud
from app.database.session import get_db
from app.utils.logger import logger

router = APIRouter(prefix="/pipeline", tags=["deal-pipeline"])

VALID_STAGES = [
    "new",
    "screening",
    "diligence",
    "ic_review",
    "term_sheet",
    "closed_won",
    "closed_lost",
    "passed",
]


class PipelineEntry(BaseModel):
    """Pipeline entry model."""
    analysis_id: str
    company_name: str
    stage: str = "new"
    priority: str = "medium"  # low, medium, high, urgent
    assigned_to: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    due_date: Optional[str] = None
    diligence_checklist: list[dict[str, Any]] = Field(default_factory=list)


class StageUpdate(BaseModel):
    """Stage transition request."""
    new_stage: str
    notes: Optional[str] = None


class PipelineUpdate(BaseModel):
    """Pipeline entry update."""
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    due_date: Optional[str] = None
    diligence_checklist: Optional[list[dict[str, Any]]] = None


@router.get(
    "/",
    summary="Get Pipeline Board",
    description="Get all deals organized by pipeline stage (Kanban view)",
)
async def get_pipeline_board(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get all deals organized by stage for Kanban display."""
    return await crud.get_pipeline_board(db)


@router.post(
    "/",
    summary="Add Deal to Pipeline",
    description="Add a new deal to the pipeline board",
)
async def add_to_pipeline(
    entry: PipelineEntry,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Add a deal to the pipeline."""
    if entry.stage not in VALID_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage: {entry.stage}. Valid: {VALID_STAGES}",
        )

    # Check for duplicate
    existing = await crud.get_pipeline_entry(db, entry.analysis_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Deal {entry.analysis_id} is already in the pipeline",
        )

    result = await crud.add_to_pipeline(
        db,
        analysis_id=entry.analysis_id,
        company_name=entry.company_name,
        stage=entry.stage,
        priority=entry.priority,
        assigned_to=entry.assigned_to,
        tags=entry.tags,
        notes=entry.notes,
        due_date=entry.due_date,
        diligence_checklist=entry.diligence_checklist,
    )

    logger.info(f"Added to pipeline: {entry.company_name} ({entry.stage})")

    return {
        "message": "Deal added to pipeline",
        "id": str(result.id),
        "entry": crud._pipeline_entry_to_dict(result),
    }


@router.put(
    "/{entry_id}/stage",
    summary="Move Deal to New Stage",
    description="Transition a deal to a new pipeline stage",
)
async def update_stage(
    entry_id: str,
    update: StageUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Move a deal to a new pipeline stage."""
    if update.new_stage not in VALID_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage: {update.new_stage}. Valid: {VALID_STAGES}",
        )

    entry = await crud.update_pipeline_stage(db, entry_id, update.new_stage, update.notes)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Pipeline entry not found: {entry_id}")

    old_stage = "unknown"
    history = entry.stage_history or []
    if len(history) >= 2:
        old_stage = history[-2].get("stage", "unknown")

    logger.info(f"Pipeline stage change: {entry.company_name} {old_stage} -> {update.new_stage}")

    return {
        "message": f"Moved from {old_stage} to {update.new_stage}",
        "entry": crud._pipeline_entry_to_dict(entry),
    }


@router.put(
    "/{entry_id}",
    summary="Update Pipeline Entry",
    description="Update pipeline entry details (priority, assignee, tags, etc.)",
)
async def update_entry(
    entry_id: str,
    update: PipelineUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update pipeline entry metadata."""
    entry = await crud.update_pipeline_entry(db, entry_id, update.model_dump())
    if not entry:
        raise HTTPException(status_code=404, detail=f"Pipeline entry not found: {entry_id}")

    return {"message": "Entry updated", "entry": crud._pipeline_entry_to_dict(entry)}


@router.delete(
    "/{entry_id}",
    summary="Remove from Pipeline",
    description="Remove a deal from the pipeline",
)
async def remove_from_pipeline(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Remove a deal from the pipeline."""
    deleted = await crud.delete_pipeline_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Pipeline entry not found: {entry_id}")

    logger.info(f"Removed from pipeline: {entry_id}")
    return {"message": f"Removed from pipeline"}


@router.post(
    "/{entry_id}/generate-checklist",
    summary="Generate Due Diligence Checklist",
    description="Auto-generate a due diligence checklist based on the deal's risk profile",
)
async def generate_checklist(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Generate a due diligence checklist from the deal's analysis results.

    Maps risk categories to standard diligence items, then adds
    deal-specific items from identified risks.
    """
    entry = await crud.get_pipeline_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Pipeline entry not found: {entry_id}")

    # Standard baseline checklist
    checklist: list[dict[str, Any]] = [
        {"item": "Review financial statements (3 years)", "category": "financial", "completed": False},
        {"item": "Verify revenue recognition policies", "category": "financial", "completed": False},
        {"item": "Validate unit economics", "category": "financial", "completed": False},
        {"item": "Cap table review", "category": "legal", "completed": False},
        {"item": "IP ownership verification", "category": "legal", "completed": False},
        {"item": "Material contracts review", "category": "legal", "completed": False},
        {"item": "Founder background checks", "category": "team", "completed": False},
        {"item": "Key employee retention assessment", "category": "team", "completed": False},
        {"item": "Customer reference calls (3+)", "category": "market", "completed": False},
        {"item": "Competitive landscape validation", "category": "market", "completed": False},
        {"item": "Technology / architecture review", "category": "operational", "completed": False},
        {"item": "Cybersecurity assessment", "category": "operational", "completed": False},
    ]

    # Try to enrich from analysis results
    from app.api.deals import _analysis_results
    analysis_result = _analysis_results.get(entry.analysis_id)

    if analysis_result and hasattr(analysis_result, "risks"):
        risks = analysis_result.risks
        if hasattr(risks, "risks"):
            for risk in risks.risks:
                severity = risk.severity.value if hasattr(risk.severity, "value") else str(risk.severity)
                if severity in ("critical", "high"):
                    checklist.append({
                        "item": f"Investigate: {risk.title}",
                        "category": risk.category,
                        "completed": False,
                        "from_risk": True,
                        "severity": severity,
                    })

        if hasattr(risks, "must_verify"):
            for item in risks.must_verify:
                checklist.append({
                    "item": item,
                    "category": "verification",
                    "completed": False,
                    "from_risk": True,
                })

    # Save to the pipeline entry
    updated = await crud.update_pipeline_entry(
        db, entry_id, {"diligence_checklist": checklist}
    )

    logger.info(f"Generated {len(checklist)} checklist items for {entry.company_name}")

    return {
        "message": f"Generated {len(checklist)} checklist items",
        "checklist": checklist,
        "entry": crud._pipeline_entry_to_dict(updated) if updated else None,
    }


@router.get(
    "/stats",
    summary="Pipeline Statistics",
    description="Get pipeline analytics and metrics",
)
async def get_pipeline_stats_endpoint(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get pipeline analytics."""
    return await crud.get_pipeline_stats(db)
