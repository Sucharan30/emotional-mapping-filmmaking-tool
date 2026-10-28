"""
services/knowledge_base.py — Knowledge base retrieval and management.
"""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from constants import (
    KNOWLEDGE_BASE_MIN_MATCH,
    KNOWLEDGE_BASE_RETRIEVAL_LIMIT,
)
from models import KnowledgeBase


async def list_knowledge_base_items(
    db: AsyncSession,
    category: Optional[str] = None,
    emotion: Optional[str] = None,
    review_status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[KnowledgeBase], int]:
    """
    List knowledge base entries with optional filtering by category, emotion,
    and review status. Returns (items, total_count).
    """
    query = select(KnowledgeBase)
    count_query = select(func.count(KnowledgeBase.id))

    if category:
        query = query.where(KnowledgeBase.category == category)
        count_query = count_query.where(KnowledgeBase.category == category)

    if emotion:
        query = query.where(KnowledgeBase.potential_emotions.contains([emotion]))
        count_query = count_query.where(KnowledgeBase.potential_emotions.contains([emotion]))

    if review_status:
        query = query.where(KnowledgeBase.review_status == review_status)
        count_query = count_query.where(KnowledgeBase.review_status == review_status)

    total = await db.scalar(count_query) or 0

    query = (
        query.order_by(KnowledgeBase.technique_name.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_kb_item_by_id(
    db: AsyncSession, kb_id: int
) -> Optional[KnowledgeBase]:
    """Retrieves a single knowledge base entry by ID."""
    query = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def retrieve_relevant_kb_items(
    db: AsyncSession, target_emotion: Optional[str]
) -> Sequence[KnowledgeBase]:
    """
    Retrieves knowledge base items matching the target emotion for Shot Designer context.
    If no emotion is provided or not enough items match, tops up with general techniques.
    """
    # Prefer reviewed items, but fall back to drafts if no reviewed items exist
    count_reviewed = await db.scalar(
        select(func.count(KnowledgeBase.id)).where(KnowledgeBase.review_status == "reviewed")
    ) or 0

    base_query = select(KnowledgeBase)
    if count_reviewed > 0:
        base_query = base_query.where(KnowledgeBase.review_status == "reviewed")

    items: list[KnowledgeBase] = []

    if target_emotion:
        match_query = base_query.where(KnowledgeBase.potential_emotions.contains([target_emotion]))
        result = await db.execute(match_query)
        items = list(result.scalars().all())

    # Top up if we need more entries for sufficient LLM context variety
    if len(items) < KNOWLEDGE_BASE_MIN_MATCH:
        shortfall = KNOWLEDGE_BASE_RETRIEVAL_LIMIT - len(items)
        exclude_ids = [item.id for item in items]

        topup_query = base_query
        if exclude_ids:
            topup_query = topup_query.where(KnowledgeBase.id.notin_(exclude_ids))

        topup_query = topup_query.order_by(KnowledgeBase.technique_name.asc()).limit(shortfall)
        topup_result = await db.execute(topup_query)
        items.extend(topup_result.scalars().all())

    return items[:KNOWLEDGE_BASE_RETRIEVAL_LIMIT]
