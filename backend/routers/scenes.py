"""
routers/scenes.py — Scenes and Shot Designer router.
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth import AuthUser, get_current_user
from db import get_db
from llm import LLMProvider, get_llm
from schemas import (
    SceneCreate,
    SceneResponse,
    SceneUpdate,
    ShotDesignerRequest,
    ShotDesignerResponse,
    ShotRecommendationResponse,
)
from services import scenes as scenes_service
from services import shot_designer as ai_service

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    data: SceneCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await scenes_service.create_scene(db, user.id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "project_not_found", "message": str(e)},
        )


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene(
    scene_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scene = await scenes_service.get_scene_by_id(db, scene_id, user.id)
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "scene_not_found", "message": "Scene not found."},
        )
    return scene


@router.patch("/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: uuid.UUID,
    data: SceneUpdate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scene = await scenes_service.update_scene(db, scene_id, user.id, data)
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "scene_not_found", "message": "Scene not found."},
        )
    return scene


@router.delete("/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    scene_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await scenes_service.delete_scene(db, scene_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "scene_not_found", "message": "Scene not found."},
        )


@router.get("/{scene_id}/recommendations", response_model=List[ShotRecommendationResponse])
async def get_scene_recommendations(
    scene_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve existing shot recommendations for an authorized scene.
    """
    scene = await scenes_service.get_scene_by_id(db, scene_id, user.id)
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "scene_not_found", "message": "Scene not found."},
        )
    return scene.shot_recommendations or []


# ── AI Orchestration ──────────────────────────────────────────────────────────

@router.post("/design-shots", response_model=ShotDesignerResponse)
async def generate_shot_recommendations(
    req: ShotDesignerRequest,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
):
    """
    Calls the LLM to generate 4-5 shot recommendations for the specified scene.
    Enforces daily rate limits, ownership, and atomic database persistence.
    """
    try:
        recs = await ai_service.generate_shot_recommendations(
            db, user.id, req.scene_id, llm
        )
    except ai_service.DailyLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "daily_limit_exceeded", "message": e.message},
        )
    except ai_service.SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "scene_not_found", "message": e.message},
        )
    except ai_service.InsufficientSceneDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "insufficient_scene_data", "message": e.message},
        )

    model_used = recs[0].model_name if recs else None

    return ShotDesignerResponse(
        scene_id=req.scene_id,
        recommendations=recs,
        model_used=model_used,
    )
