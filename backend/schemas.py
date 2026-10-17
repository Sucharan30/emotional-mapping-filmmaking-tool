"""
schemas.py — Pydantic v2 request/response models.

These define the API contract — what the frontend sends and receives.
All validation against controlled vocabularies reads from constants.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator

from constants import (
    BUDGET_FIT_LEVELS,
    BUDGET_LEVELS,
    CHARACTER_FOCUS_OPTIONS,
    COMPLEXITY_LEVELS,
    EMOTIONS,
    KB_CATEGORIES,
    KB_REVIEW_STATUS,
    PROJECT_TYPES,
    BUDGET_NOTES_MAX_CHARS,
    PROJECT_NAME_MAX_CHARS,
    SCENE_DESCRIPTION_MAX_CHARS,
    SCENE_DESCRIPTION_MIN_CHARS,
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class AuthMeResponse(BaseModel):
    id: uuid.UUID
    email: str


# ── Meta ──────────────────────────────────────────────────────────────────────

class MetaOptionsResponse(BaseModel):
    emotions: List[str]
    budget_levels: List[str]
    character_focus_options: List[str]
    complexity_levels: List[str]
    budget_fit_levels: List[str]
    project_types: List[str]
    kb_categories: List[str]
    kb_review_status: List[str]


# ── Projects ──────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=PROJECT_NAME_MAX_CHARS)
    type: str = Field("shot_design")
    description: Optional[str] = None

    @field_validator("type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        if v not in PROJECT_TYPES:
            raise ValueError(f"type must be one of: {PROJECT_TYPES}")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=PROJECT_NAME_MAX_CHARS)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    scenes: Optional[List[SceneResponse]] = None


# ── Scenes ────────────────────────────────────────────────────────────────────

class SceneCreate(BaseModel):
    project_id: uuid.UUID
    description: str = Field(
        ...,
        min_length=SCENE_DESCRIPTION_MIN_CHARS,
        max_length=SCENE_DESCRIPTION_MAX_CHARS,
    )
    target_emotion: Optional[str] = None
    character_focus: Optional[str] = None
    production_budget: str = Field("medium")
    budget_notes: Optional[str] = Field(None, max_length=BUDGET_NOTES_MAX_CHARS)

    @field_validator("target_emotion")
    @classmethod
    def emotion_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EMOTIONS:
            raise ValueError(f"target_emotion must be one of: {EMOTIONS}")
        return v

    @field_validator("character_focus")
    @classmethod
    def focus_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CHARACTER_FOCUS_OPTIONS:
            raise ValueError(f"character_focus must be one of: {CHARACTER_FOCUS_OPTIONS}")
        return v

    @field_validator("production_budget")
    @classmethod
    def budget_must_be_valid(cls, v: str) -> str:
        if v not in BUDGET_LEVELS:
            raise ValueError(f"production_budget must be one of: {BUDGET_LEVELS}")
        return v


class SceneUpdate(BaseModel):
    description: Optional[str] = Field(
        None,
        min_length=SCENE_DESCRIPTION_MIN_CHARS,
        max_length=SCENE_DESCRIPTION_MAX_CHARS,
    )
    target_emotion: Optional[str] = None
    character_focus: Optional[str] = None
    production_budget: Optional[str] = None
    budget_notes: Optional[str] = Field(None, max_length=BUDGET_NOTES_MAX_CHARS)

    @field_validator("target_emotion")
    @classmethod
    def emotion_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EMOTIONS:
            raise ValueError(f"target_emotion must be one of: {EMOTIONS}")
        return v

    @field_validator("character_focus")
    @classmethod
    def focus_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CHARACTER_FOCUS_OPTIONS:
            raise ValueError(f"character_focus must be one of: {CHARACTER_FOCUS_OPTIONS}")
        return v

    @field_validator("production_budget")
    @classmethod
    def budget_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in BUDGET_LEVELS:
            raise ValueError(f"production_budget must be one of: {BUDGET_LEVELS}")
        return v


class SceneResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    description: str
    target_emotion: Optional[str] = None
    character_focus: Optional[str] = None
    production_budget: str
    budget_notes: Optional[str] = None
    video_url: Optional[str] = None
    video_analysis: Optional[Any] = None
    experiment_group_id: Optional[uuid.UUID] = None
    variant_label: Optional[str] = None
    created_at: datetime
    shot_recommendations: Optional[List[ShotRecommendationResponse]] = None


# ── Knowledge Base ────────────────────────────────────────────────────────────

class KnowledgeBaseResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    technique_name: str
    category: str
    visual_characteristic: str
    potential_emotions: List[str]
    context_note: str
    example_scene: Optional[str] = None
    equipment_needs: Optional[str] = None
    typical_complexity: str
    review_status: str
    source_note: Optional[str] = None
    created_at: datetime


class KnowledgeBaseListResponse(BaseModel):
    items: List[KnowledgeBaseResponse]
    total: int
    limit: int
    offset: int


# ── Shot Recommendations ──────────────────────────────────────────────────────

class ProductionComplexity(BaseModel):
    level: str
    reason: str

    @field_validator("level")
    @classmethod
    def level_must_be_valid(cls, v: str) -> str:
        if v not in COMPLEXITY_LEVELS:
            raise ValueError(f"level must be one of: {COMPLEXITY_LEVELS}")
        return v


class BudgetFit(BaseModel):
    level: str
    reason: str

    @field_validator("level")
    @classmethod
    def level_must_be_valid(cls, v: str) -> str:
        if v not in BUDGET_FIT_LEVELS:
            raise ValueError(f"level must be one of: {BUDGET_FIT_LEVELS}")
        return v


class LLMShotRecommendation(BaseModel):
    """Schema the LLM must output for each recommendation."""
    rank: int
    perspective_name: str
    reasoning: str
    visual_checklist: List[str]
    context_caveat: str
    production_complexity: ProductionComplexity
    budget_fit: BudgetFit
    knowledge_base_ids: List[str] = Field(default_factory=list)


class LLMShotDesignerOutput(BaseModel):
    """Top-level schema the LLM must output."""
    recommendations: List[LLMShotRecommendation]


class ShotRecommendationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    scene_id: uuid.UUID
    rank: int
    perspective_name: str
    reasoning: str
    visual_checklist: List[str]
    context_caveat: str
    production_complexity_level: str
    production_complexity_reason: str
    budget_fit: str
    budget_fit_reason: str
    knowledge_base_ids: List[str]
    model_name: Optional[str] = None
    created_at: datetime


class ShotDesignerRequest(BaseModel):
    scene_id: uuid.UUID


class ShotDesignerResponse(BaseModel):
    scene_id: uuid.UUID
    recommendations: List[ShotRecommendationResponse]
    model_used: Optional[str] = None


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedProjectsResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    limit: int
    offset: int


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Rebuild forward references
ProjectResponse.model_rebuild()
SceneResponse.model_rebuild()
