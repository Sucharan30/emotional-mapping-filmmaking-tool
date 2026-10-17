"""
services/shot_designer.py — AI Orchestration for Shot Recommendations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Set

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from constants import (
    FEATURE_SHOT_DESIGNER,
    SCENE_DESCRIPTION_MIN_CHARS,
    SHOT_RECS_MAX,
    SHOT_RECS_MIN,
)
from llm.base import LLMProvider, LLMValidationError
from models import AiUsage, ShotRecommendation
from prompts.shot_designer import SHOT_DESIGNER_SYSTEM_PROMPT
from schemas import LLMShotDesignerOutput
from services.knowledge_base import retrieve_relevant_kb_items
from services.scenes import get_scene_by_id

logger = logging.getLogger(__name__)


class DailyLimitExceededError(Exception):
    """Raised when a user exceeds their daily AI generation allowance."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SceneNotFoundError(Exception):
    """Raised when a scene is not found or not owned by the user."""
    def __init__(self, message: str = "Scene not found or access denied.") -> None:
        super().__init__(message)
        self.message = message


class InsufficientSceneDataError(Exception):
    """Raised when a scene lacks sufficient detail for generation."""
    def __init__(self, message: str = "Scene description is too short to design shots.") -> None:
        super().__init__(message)
        self.message = message


async def get_daily_generation_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Returns the number of successful Shot Designer runs today (UTC)."""
    now_utc = datetime.now(timezone.utc)
    today_utc_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)

    query = select(func.count(AiUsage.id)).where(
        AiUsage.user_id == user_id,
        AiUsage.feature == FEATURE_SHOT_DESIGNER,
        AiUsage.created_at >= today_utc_start,
    )
    count = await db.scalar(query)
    return count or 0


async def generate_shot_recommendations(
    db: AsyncSession,
    user_id: uuid.UUID,
    scene_id: uuid.UUID,
    llm: LLMProvider,
) -> List[ShotRecommendation]:
    """
    Orchestrates Shot Designer recommendation generation:
    1. Enforces user daily AI generation limit.
    2. Verifies scene existence and ownership.
    3. Validates minimum scene description length.
    4. Retrieves relevant knowledge base items.
    5. Invokes LLM with system and user prompts.
    6. Validates recommendations count (4-5) and sanitizes KB ID references.
    7. Atomically saves recommendations and records AI usage.
    """
    # 1. Enforce Daily AI Limit
    current_usage = await get_daily_generation_count(db, user_id)
    if current_usage >= settings.daily_ai_generation_limit:
        raise DailyLimitExceededError(
            f"Daily AI generation limit reached ({settings.daily_ai_generation_limit} runs/day). "
            f"Limit resets at 00:00 UTC."
        )

    # 2. Fetch Scene & Verify Ownership
    scene = await get_scene_by_id(db, scene_id, user_id)
    if not scene:
        raise SceneNotFoundError()

    # 3. Check Minimum Scene Content
    if not scene.description or len(scene.description.strip()) < SCENE_DESCRIPTION_MIN_CHARS:
        raise InsufficientSceneDataError(
            f"Scene description must be at least {SCENE_DESCRIPTION_MIN_CHARS} characters."
        )

    # 4. Gather Knowledge Base Context
    kb_items = await retrieve_relevant_kb_items(db, scene.target_emotion)
    valid_kb_id_strings: Set[str] = {str(item.id) for item in kb_items}

    kb_context_lines = []
    for item in kb_items:
        emotions_str = ", ".join(item.potential_emotions) if item.potential_emotions else "None"
        kb_context_lines.append(
            f"- ID: {item.id}\n"
            f"  Technique: {item.technique_name} (Category: {item.category})\n"
            f"  Visual Characteristics: {item.visual_characteristic}\n"
            f"  Potential Emotions: {emotions_str}\n"
            f"  Contextual Notes: {item.context_note}"
        )
    kb_context = "\n\n".join(kb_context_lines) if kb_context_lines else "No specific techniques available."

    user_prompt = f"""SCENE DETAILS:
- Description: {scene.description}
- Target Emotion: {scene.target_emotion or 'Neutral / Open'}
- Character Focus: {scene.character_focus or 'Neutral Observer'}
- Production Budget: {scene.production_budget}
- Budget Notes: {scene.budget_notes or 'None specified'}

KNOWLEDGE BASE CONTEXT:
{kb_context}
"""

    # 5. Call LLM
    output, usage = await llm.generate_structured(
        system_prompt=SHOT_DESIGNER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=LLMShotDesignerOutput,
    )

    # 6. Post-generation Validation
    recs_count = len(output.recommendations)
    if recs_count < SHOT_RECS_MIN or recs_count > SHOT_RECS_MAX:
        logger.warning(
            "LLM returned %s recommendations, expected between %s and %s",
            recs_count, SHOT_RECS_MIN, SHOT_RECS_MAX
        )
        # If model returned slightly outside range, clamp or validate
        if recs_count < SHOT_RECS_MIN:
            raise LLMValidationError(
                f"The AI generated only {recs_count} recommendations. Expected at least {SHOT_RECS_MIN}."
            )

    # 7. Atomic Transactional Persistence
    try:
        # Delete previous recommendations for this scene
        await db.execute(
            delete(ShotRecommendation).where(ShotRecommendation.scene_id == scene.id)
        )

        new_recs: List[ShotRecommendation] = []
        for idx, rec in enumerate(output.recommendations[:SHOT_RECS_MAX], start=1):
            # Anti-hallucination filter: Keep only IDs that were actually in the context
            filtered_kb_ids = [
                str(raw_id) for raw_id in rec.knowledge_base_ids
                if str(raw_id) in valid_kb_id_strings
            ]

            db_rec = ShotRecommendation(
                scene_id=scene.id,
                rank=idx,
                perspective_name=rec.perspective_name,
                reasoning=rec.reasoning,
                visual_checklist=rec.visual_checklist,
                context_caveat=rec.context_caveat,
                production_complexity_level=rec.production_complexity.level,
                production_complexity_reason=rec.production_complexity.reason,
                budget_fit=rec.budget_fit.level,
                budget_fit_reason=rec.budget_fit.reason,
                knowledge_base_ids=filtered_kb_ids,
                model_name=usage.model,
            )
            db.add(db_rec)
            new_recs.append(db_rec)

        # Log AI Usage
        usage_log = AiUsage(
            user_id=user_id,
            feature=FEATURE_SHOT_DESIGNER,
            model_name=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )
        db.add(usage_log)

        await db.commit()

        for rec in new_recs:
            await db.refresh(rec)

        return new_recs

    except Exception as exc:
        await db.rollback()
        logger.error("Failed to commit shot recommendations to database: %s", exc)
        raise
