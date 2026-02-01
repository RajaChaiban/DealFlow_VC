"""
CRUD operations for DealFlow AI Copilot.

Provides database access functions for users, analyses, pipeline, and chat.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ChatMessage, DealAnalysis, DealPipelineEntry, User
from app.utils.logger import logger


# =============================================================================
# User CRUD
# =============================================================================


async def create_user(
    db: AsyncSession,
    email: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    organization: Optional[str] = None,
    role: str = "analyst",
) -> User:
    """Create a new user."""
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        organization=organization,
        role=role,
    )
    db.add(user)
    await db.flush()
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by UUID string."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def get_user_by_api_key(db: AsyncSession, api_key: str) -> Optional[User]:
    """Get user by API key."""
    result = await db.execute(select(User).where(User.api_key == api_key))
    return result.scalar_one_or_none()


async def update_user_api_key(db: AsyncSession, user_id: str, api_key: str) -> Optional[User]:
    """Update a user's API key."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.api_key = api_key
        await db.flush()
    return user


# =============================================================================
# Deal Analysis CRUD
# =============================================================================


async def save_analysis(
    db: AsyncSession,
    analysis_id: str,
    company_name: str,
    status: str = "completed",
    result_json: Optional[dict] = None,
    processing_time: Optional[float] = None,
) -> DealAnalysis:
    """Save or update a deal analysis."""
    # Check if exists
    existing = await db.execute(
        select(DealAnalysis).where(DealAnalysis.analysis_id == analysis_id)
    )
    analysis = existing.scalar_one_or_none()

    if analysis:
        analysis.status = status
        if result_json:
            analysis.full_ic_memo = result_json
            summary = result_json.get("summary", {})
            analysis.recommendation = summary.get("recommendation")
            analysis.conviction_level = summary.get("conviction")
            analysis.overall_attractiveness_score = summary.get("analysis_score")
            analysis.overall_risk_score = summary.get("risk_score")
            valuation = result_json.get("valuation", {})
            analysis.valuation_low = valuation.get("valuation_low")
            analysis.valuation_mid = valuation.get("valuation_mid")
            analysis.valuation_high = valuation.get("valuation_high")
        if processing_time:
            analysis.processing_time_seconds = processing_time
        if status == "completed":
            analysis.completed_at = datetime.utcnow()
        analysis.company_name = company_name
    else:
        analysis = DealAnalysis(
            analysis_id=analysis_id,
            company_name=company_name,
            status=status,
            full_ic_memo=result_json,
            processing_time_seconds=processing_time,
        )
        if result_json:
            summary = result_json.get("summary", {})
            analysis.recommendation = summary.get("recommendation")
            analysis.conviction_level = summary.get("conviction")
            analysis.overall_attractiveness_score = summary.get("analysis_score")
            analysis.overall_risk_score = summary.get("risk_score")
            valuation = result_json.get("valuation", {})
            analysis.valuation_low = valuation.get("valuation_low")
            analysis.valuation_mid = valuation.get("valuation_mid")
            analysis.valuation_high = valuation.get("valuation_high")
        if status == "completed":
            analysis.completed_at = datetime.utcnow()
        db.add(analysis)

    await db.flush()
    return analysis


async def get_analysis(db: AsyncSession, analysis_id: str) -> Optional[DealAnalysis]:
    """Get analysis by string analysis_id."""
    result = await db.execute(
        select(DealAnalysis).where(DealAnalysis.analysis_id == analysis_id)
    )
    return result.scalar_one_or_none()


async def list_analyses(
    db: AsyncSession,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[DealAnalysis], int]:
    """List analyses with optional status filter."""
    query = select(DealAnalysis).order_by(DealAnalysis.created_at.desc())
    if status:
        query = query.where(DealAnalysis.status == status)
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    analyses = list(result.scalars().all())

    # Count total
    from sqlalchemy import func
    count_query = select(func.count(DealAnalysis.id))
    if status:
        count_query = count_query.where(DealAnalysis.status == status)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return analyses, total


async def delete_analysis(db: AsyncSession, analysis_id: str) -> bool:
    """Delete an analysis."""
    result = await db.execute(
        delete(DealAnalysis).where(DealAnalysis.analysis_id == analysis_id)
    )
    await db.flush()
    return result.rowcount > 0


# =============================================================================
# Pipeline CRUD
# =============================================================================


async def add_to_pipeline(
    db: AsyncSession,
    analysis_id: str,
    company_name: str,
    stage: str = "new",
    priority: str = "medium",
    assigned_to: Optional[str] = None,
    tags: Optional[list[str]] = None,
    notes: Optional[str] = None,
    due_date: Optional[str] = None,
    diligence_checklist: Optional[list[dict]] = None,
) -> DealPipelineEntry:
    """Add a deal to the pipeline."""
    now = datetime.utcnow()
    entry = DealPipelineEntry(
        analysis_id=analysis_id,
        company_name=company_name,
        stage=stage,
        priority=priority,
        assigned_to=assigned_to,
        tags=tags or [],
        notes=notes,
        diligence_checklist=diligence_checklist or [],
        stage_history=[{"stage": stage, "entered_at": now.isoformat()}],
    )
    db.add(entry)
    await db.flush()
    return entry


PIPELINE_STAGES = [
    "new", "screening", "diligence", "ic_review",
    "term_sheet", "closed_won", "closed_lost", "passed",
]


async def get_pipeline_board(db: AsyncSession) -> dict[str, Any]:
    """Get all pipeline entries organized by stage."""
    VALID_STAGES = PIPELINE_STAGES

    result = await db.execute(
        select(DealPipelineEntry).order_by(DealPipelineEntry.created_at.desc())
    )
    entries = list(result.scalars().all())

    board: dict[str, list[dict]] = {stage: [] for stage in VALID_STAGES}
    counts: dict[str, int] = {stage: 0 for stage in VALID_STAGES}

    for entry in entries:
        stage = entry.stage or "new"
        if stage in board:
            board[stage].append(_pipeline_entry_to_dict(entry))
            counts[stage] += 1

    active_stages = ["screening", "diligence", "ic_review", "term_sheet"]
    active_count = sum(counts.get(s, 0) for s in active_stages)

    return {
        "stages": VALID_STAGES,
        "board": board,
        "counts": counts,
        "total_deals": len(entries),
        "active_deals": active_count,
    }


async def get_pipeline_entry(db: AsyncSession, analysis_id: str) -> Optional[DealPipelineEntry]:
    """Get pipeline entry by analysis_id."""
    result = await db.execute(
        select(DealPipelineEntry).where(DealPipelineEntry.analysis_id == analysis_id)
    )
    return result.scalar_one_or_none()


async def update_pipeline_stage(
    db: AsyncSession,
    analysis_id: str,
    new_stage: str,
    notes: Optional[str] = None,
) -> Optional[DealPipelineEntry]:
    """Move a deal to a new pipeline stage."""
    entry = await get_pipeline_entry(db, analysis_id)
    if not entry:
        return None

    old_stage = entry.stage
    now = datetime.utcnow()

    # Update stage history — deep copy so SQLAlchemy detects the mutation
    import copy
    history = copy.deepcopy(entry.stage_history or [])
    if history:
        history[-1]["exited_at"] = now.isoformat()
    history.append({
        "stage": new_stage,
        "entered_at": now.isoformat(),
        "notes": notes,
    })

    entry.stage = new_stage
    entry.stage_history = history
    entry.stage_entered_at = now
    entry.updated_at = now

    await db.flush()
    return entry


async def update_pipeline_entry(
    db: AsyncSession,
    analysis_id: str,
    updates: dict[str, Any],
) -> Optional[DealPipelineEntry]:
    """Update pipeline entry metadata."""
    entry = await get_pipeline_entry(db, analysis_id)
    if not entry:
        return None

    if "priority" in updates and updates["priority"] is not None:
        entry.priority = updates["priority"]
    if "assigned_to" in updates and updates["assigned_to"] is not None:
        entry.assigned_to = updates["assigned_to"]
    if "tags" in updates and updates["tags"] is not None:
        entry.tags = updates["tags"]
    if "notes" in updates and updates["notes"] is not None:
        entry.notes = updates["notes"]
    if "due_date" in updates and updates["due_date"] is not None:
        entry.due_date = updates["due_date"]
    if "diligence_checklist" in updates and updates["diligence_checklist"] is not None:
        checklist = updates["diligence_checklist"]
        entry.diligence_checklist = checklist
        completed = sum(1 for item in checklist if item.get("completed"))
        total = len(checklist)
        entry.diligence_completion_pct = (completed / total * 100) if total > 0 else 0

    entry.updated_at = datetime.utcnow()
    await db.flush()
    return entry


async def delete_pipeline_entry(db: AsyncSession, analysis_id: str) -> bool:
    """Remove a deal from the pipeline."""
    result = await db.execute(
        delete(DealPipelineEntry).where(DealPipelineEntry.analysis_id == analysis_id)
    )
    await db.flush()
    return result.rowcount > 0


async def get_pipeline_stats(db: AsyncSession) -> dict[str, Any]:
    """Get pipeline statistics."""
    VALID_STAGES = PIPELINE_STAGES

    result = await db.execute(select(DealPipelineEntry))
    entries = list(result.scalars().all())

    stage_counts = {stage: 0 for stage in VALID_STAGES}
    priority_counts = {"low": 0, "medium": 0, "high": 0, "urgent": 0}

    for entry in entries:
        if entry.stage in stage_counts:
            stage_counts[entry.stage] += 1
        if entry.priority in priority_counts:
            priority_counts[entry.priority] += 1

    active_stages = ["screening", "diligence", "ic_review", "term_sheet"]
    active_deals = sum(stage_counts.get(s, 0) for s in active_stages)

    diligence_entries = [e for e in entries if e.diligence_completion_pct and e.diligence_completion_pct > 0]
    avg_diligence = (
        sum(e.diligence_completion_pct for e in diligence_entries) / len(diligence_entries)
        if diligence_entries
        else 0
    )

    return {
        "total_deals": len(entries),
        "active_deals": active_deals,
        "stage_distribution": stage_counts,
        "priority_distribution": priority_counts,
        "avg_diligence_completion": round(avg_diligence, 1),
        "conversion_rate": (
            stage_counts.get("closed_won", 0) / max(len(entries), 1) * 100
        ),
    }


def _pipeline_entry_to_dict(entry: DealPipelineEntry) -> dict[str, Any]:
    """Convert pipeline entry to API dict."""
    return {
        "id": str(entry.id),
        "analysis_id": entry.analysis_id,
        "company_name": entry.company_name,
        "stage": entry.stage,
        "priority": entry.priority,
        "assigned_to": entry.assigned_to,
        "tags": entry.tags or [],
        "notes": entry.notes,
        "due_date": entry.due_date.isoformat() if entry.due_date else None,
        "diligence_checklist": entry.diligence_checklist or [],
        "diligence_completion_pct": entry.diligence_completion_pct or 0,
        "stage_history": entry.stage_history or [],
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


# =============================================================================
# Chat CRUD
# =============================================================================


async def save_chat_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    analysis_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> ChatMessage:
    """Save a chat message."""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        analysis_id=analysis_id,
        message_metadata=metadata,
    )
    db.add(message)
    await db.flush()
    return message


async def get_chat_history(
    db: AsyncSession,
    session_id: str,
    limit: int = 50,
) -> list[ChatMessage]:
    """Get chat messages for a session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_chat_sessions(db: AsyncSession) -> list[dict[str, Any]]:
    """List all chat sessions."""
    from sqlalchemy import func, distinct

    # Get distinct session IDs with counts and dates
    result = await db.execute(
        select(
            ChatMessage.session_id,
            ChatMessage.analysis_id,
            func.count(ChatMessage.id).label("message_count"),
            func.min(ChatMessage.created_at).label("created_at"),
        )
        .group_by(ChatMessage.session_id, ChatMessage.analysis_id)
        .order_by(func.max(ChatMessage.created_at).desc())
    )

    sessions = []
    for row in result.all():
        sessions.append({
            "session_id": row.session_id,
            "analysis_id": row.analysis_id,
            "message_count": row.message_count,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    return sessions


async def delete_chat_session(db: AsyncSession, session_id: str) -> int:
    """Delete all messages in a chat session. Returns count deleted."""
    result = await db.execute(
        delete(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    await db.flush()
    return result.rowcount
