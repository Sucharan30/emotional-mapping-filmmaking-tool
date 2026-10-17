"""
routers/knowledge_base.py — Knowledge base router.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth import AuthUser, get_current_user
from constants import EMOTIONS, KB_CATEGORIES, KB_REVIEW_STATUS
from db import get_db
from schemas import KnowledgeBaseListResponse, KnowledgeBaseResponse
from services import knowledge_base as kb_service

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_base(
    category: Optional[str] = Query(None, description=f"Filter by category: {KB_CATEGORIES}"),
    emotion: Optional[str] = Query(None, description=f"Filter by potential emotion: {EMOTIONS}"),
    review_status: Optional[str] = Query(None, description=f"Filter by review status: {KB_REVIEW_STATUS}"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List cinematography techniques from the knowledge base with optional filters.
    Requires authentication.
    """
    if category is not None and category not in KB_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_filter",
                "message": f"Invalid category '{category}'. Allowed: {KB_CATEGORIES}",
            },
        )

    if emotion is not None and emotion not in EMOTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_filter",
                "message": f"Invalid emotion '{emotion}'. Allowed: {EMOTIONS}",
            },
        )

    if review_status is not None and review_status not in KB_REVIEW_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_filter",
                "message": f"Invalid review_status '{review_status}'. Allowed: {KB_REVIEW_STATUS}",
            },
        )

    items, total = await kb_service.list_knowledge_base_items(
        db=db,
        category=category,
        emotion=emotion,
        review_status=review_status,
        limit=limit,
        offset=offset,
    )
    return KnowledgeBaseListResponse(
        items=list(items), total=total, limit=limit, offset=offset
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base_item(
    kb_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single knowledge base entry by UUID.
    """
    item = await kb_service.get_kb_item_by_id(db, kb_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": "Knowledge base technique not found.",
            },
        )
    return item
