"""
SQLAlchemy models for DealFlow AI Copilot.

Defines persistent storage models for deals, analyses, pipeline tracking,
and user management.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model for authentication and tracking."""

    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    role = Column(String(50), default="analyst")  # analyst, partner, admin
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    analyses = relationship("DealAnalysis", back_populates="user")
    pipeline_entries = relationship("DealPipelineEntry", back_populates="user")


class DealAnalysis(Base):
    """Persisted deal analysis with full IC memo data."""

    __tablename__ = "deal_analyses"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    analysis_id = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)

    # Company Info
    company_name = Column(String(255), nullable=False, index=True)
    industry = Column(String(255), nullable=True)
    stage = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    # File Info
    original_filename = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), default="pending", index=True)  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    # Results (stored as JSON for flexibility)
    extraction_result = Column(JSON, nullable=True)
    analysis_result = Column(JSON, nullable=True)
    risk_result = Column(JSON, nullable=True)
    valuation_result = Column(JSON, nullable=True)
    executive_summary = Column(JSON, nullable=True)
    full_ic_memo = Column(JSON, nullable=True)

    # Scores (denormalized for querying)
    overall_attractiveness_score = Column(Float, nullable=True)
    overall_risk_score = Column(Float, nullable=True)
    valuation_low = Column(Float, nullable=True)
    valuation_mid = Column(Float, nullable=True)
    valuation_high = Column(Float, nullable=True)
    recommendation = Column(String(50), nullable=True)
    conviction_level = Column(String(20), nullable=True)

    # Confidence heatmap data
    confidence_heatmap = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="analyses")

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a lightweight summary for listing."""
        return {
            "id": str(self.id),
            "analysis_id": self.analysis_id,
            "company_name": self.company_name,
            "industry": self.industry,
            "stage": self.stage,
            "status": self.status,
            "recommendation": self.recommendation,
            "conviction_level": self.conviction_level,
            "overall_attractiveness_score": self.overall_attractiveness_score,
            "overall_risk_score": self.overall_risk_score,
            "valuation_mid": self.valuation_mid,
            "processing_time_seconds": self.processing_time_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DealPipelineEntry(Base):
    """Deal pipeline / Kanban board tracking."""

    __tablename__ = "deal_pipeline"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    analysis_id = Column(String(50), nullable=False, unique=True, index=True)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)

    # Company info (denormalized for fast reads)
    company_name = Column(String(255), nullable=False, default="Unknown")

    # Pipeline Stage
    stage = Column(
        String(50),
        default="new",
        nullable=False,
        index=True,
    )  # new, screening, diligence, ic_review, term_sheet, closed_won, closed_lost, passed

    # Deal metadata
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    assigned_to = Column(String(255), nullable=True)
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)

    # Due diligence tracking
    diligence_checklist = Column(JSON, default=list)
    diligence_completion_pct = Column(Float, default=0.0)

    # Timeline
    stage_entered_at = Column(DateTime(timezone=True), server_default=func.now())
    stage_history = Column(JSON, default=list)  # [{stage, entered_at, exited_at}]
    due_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="pipeline_entries")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "analysis_id": str(self.analysis_id),
            "stage": self.stage,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "tags": self.tags or [],
            "notes": self.notes,
            "diligence_completion_pct": self.diligence_completion_pct,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "stage_entered_at": self.stage_entered_at.isoformat() if self.stage_entered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChatMessage(Base):
    """Chat messages for conversational deal analysis."""

    __tablename__ = "chat_messages"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id = Column(String(50), nullable=False, index=True)
    analysis_id = Column(String(20), nullable=True, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
