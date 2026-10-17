"""
models.py — SQLAlchemy 2.0 ORM models.

These map exactly to the tables in sql/001_foundation.sql and
sql/002_later_modules.sql. Keep models in sync with migrations.

Later-module models (Persona, AudienceFeedback, ExperimentResponse)
are defined here so SQLAlchemy's relationship system works correctly,
even though no router/service exists for them yet.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


# ── Projects ──────────────────────────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    scenes: Mapped[list[Scene]] = relationship(
        "Scene",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Scene.created_at",
    )


# ── Knowledge Base ────────────────────────────────────────────────────────────

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    technique_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    visual_characteristic: Mapped[str] = mapped_column(Text, nullable=False)
    potential_emotions: Mapped[list] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    context_note: Mapped[str] = mapped_column(Text, nullable=False)
    example_scene: Mapped[Optional[str]] = mapped_column(Text)
    equipment_needs: Mapped[Optional[str]] = mapped_column(Text)
    typical_complexity: Mapped[str] = mapped_column(Text, nullable=False)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    source_note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )


# ── Scenes ────────────────────────────────────────────────────────────────────

class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_emotion: Mapped[Optional[str]] = mapped_column(Text)
    character_focus: Mapped[Optional[str]] = mapped_column(Text)
    production_budget: Mapped[str] = mapped_column(Text, nullable=False, default="medium")
    budget_notes: Mapped[Optional[str]] = mapped_column(Text)
    video_url: Mapped[Optional[str]] = mapped_column(Text)
    video_analysis: Mapped[Optional[Any]] = mapped_column(JSONB)
    experiment_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    variant_label: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    project: Mapped[Project] = relationship("Project", back_populates="scenes")
    shot_recommendations: Mapped[list[ShotRecommendation]] = relationship(
        "ShotRecommendation",
        back_populates="scene",
        cascade="all, delete-orphan",
        order_by="ShotRecommendation.rank",
    )


# ── Shot Recommendations ──────────────────────────────────────────────────────

class ShotRecommendation(Base):
    __tablename__ = "shot_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    perspective_name: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    visual_checklist: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    context_caveat: Mapped[str] = mapped_column(Text, nullable=False)
    production_complexity_level: Mapped[str] = mapped_column(Text, nullable=False)
    production_complexity_reason: Mapped[str] = mapped_column(Text, nullable=False)
    budget_fit: Mapped[str] = mapped_column(Text, nullable=False)
    budget_fit_reason: Mapped[str] = mapped_column(Text, nullable=False)
    knowledge_base_ids: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    model_name: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    scene: Mapped[Scene] = relationship("Scene", back_populates="shot_recommendations")


# ── AI Usage ──────────────────────────────────────────────────────────────────

class AiUsage(Base):
    __tablename__ = "ai_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    feature: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(Text)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_ai_usage_user_created", "user_id", "created_at"),
    )


# ── Later-module models (schema only — no endpoints yet) ─────────────────────

class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    age_range: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(Text)
    cultural_context: Mapped[Optional[str]] = mapped_column(Text)
    film_familiarity: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )


class AudienceFeedback(Base):
    __tablename__ = "audience_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
    )
    persona_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="SET NULL"),
    )
    empathy_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    perceived_power_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    blame_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    emotional_intensity_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    overall_interpretation: Mapped[Optional[str]] = mapped_column(Text)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    model_name: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )


class ExperimentResponse(Base):
    __tablename__ = "experiment_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_code: Mapped[str] = mapped_column(Text, nullable=False)
    empathy_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    perceived_power_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    blame_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    emotional_intensity_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
