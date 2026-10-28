"""
models.py — SQLAlchemy 2.0 ORM models.

Reconciled to match the actual Supabase database schema:
  - projects.id: UUID
  - scenes.id, shot_recommendations.id, knowledge_base.id: Integer (int4)
  - personas.id, audience_feedback.id, experiment_responses.id: Integer (int4)
  - ai_usage.id: UUID
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
    # Nullable so existing unassigned projects do not crash the ORM
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        default=func.now(),
        onupdate=func.now(),
    )

    scenes: Mapped[list[Scene]] = relationship(
        "Scene",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Scene.created_at",
        lazy="selectin",
    )


# ── Knowledge Base ────────────────────────────────────────────────────────────

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    technique_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    visual_characteristic: Mapped[str] = mapped_column(Text, nullable=False)
    potential_emotions: Mapped[list] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    context_note: Mapped[str] = mapped_column(Text, nullable=False)
    example_scene: Mapped[Optional[str]] = mapped_column(Text)
    equipment_needs: Mapped[Optional[str]] = mapped_column(Text)
    typical_complexity: Mapped[Optional[str]] = mapped_column(Text, default="Low")
    review_status: Mapped[Optional[str]] = mapped_column(Text, default="draft")
    source_note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), default=func.now()
    )


# ── Scenes ────────────────────────────────────────────────────────────────────

class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
    experiment_group_id: Mapped[Optional[int]] = mapped_column(Integer)
    variant_label: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), default=func.now()
    )

    project: Mapped[Project] = relationship("Project", back_populates="scenes")
    shot_recommendations: Mapped[list[ShotRecommendation]] = relationship(
        "ShotRecommendation",
        back_populates="scene",
        cascade="all, delete-orphan",
        order_by="ShotRecommendation.rank",
        lazy="selectin",
    )


# ── Shot Recommendations ──────────────────────────────────────────────────────

class ShotRecommendation(Base):
    __tablename__ = "shot_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    perspective_name: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    visual_checklist: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    context_caveat: Mapped[str] = mapped_column(Text, nullable=False, default="")
    production_complexity_level: Mapped[str] = mapped_column(Text, nullable=False)
    production_complexity_reason: Mapped[str] = mapped_column(Text, nullable=False)
    budget_fit: Mapped[str] = mapped_column(Text, nullable=False, default="good_fit")
    budget_fit_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    knowledge_base_ids: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    model_name: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), default=func.now()
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
        TIMESTAMP(timezone=True), server_default=func.now(), default=func.now()
    )

    __table_args__ = (
        Index("idx_ai_usage_user_created", "user_id", "created_at"),
    )


# ── Later-module models (Preserving existing tables) ──────────────────────────

class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    age_range: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(Text)
    cultural_context: Mapped[Optional[str]] = mapped_column(Text)
    film_familiarity: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), default=func.now()
    )


class AudienceFeedback(Base):
    __tablename__ = "audience_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
    )
    persona_id: Mapped[Optional[int]] = mapped_column(
        Integer,
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
        TIMESTAMP(timezone=True), server_default=func.now(), default=func.now()
    )


class ExperimentResponse(Base):
    __tablename__ = "experiment_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_code: Mapped[str] = mapped_column(Text, nullable=False)
    empathy_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    perceived_power_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    blame_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    emotional_intensity_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), default=func.now()
    )
