"""
services/scenes.py — Scene lifecycle management.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Project, Scene
from schemas import SceneCreate, SceneUpdate


async def create_scene(
    db: AsyncSession, user_id: uuid.UUID, data: SceneCreate
) -> Scene:
    """Creates a scene if the user owns the parent project (or in dev unassigned mode)."""
    # Verify project ownership first
    project_query = select(Project).where(
        Project.id == data.project_id,
        or_(Project.user_id == user_id, Project.user_id.is_(None)),
    )
    project_result = await db.execute(project_query)
    if project_result.scalar_one_or_none() is None:
        raise ValueError("Project not found or access denied")

    scene = Scene(
        project_id=data.project_id,
        description=data.description,
        target_emotion=data.target_emotion,
        character_focus=data.character_focus,
        production_budget=data.production_budget,
        budget_notes=data.budget_notes,
    )
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene


async def get_scene_by_id(
    db: AsyncSession, scene_id: int, user_id: uuid.UUID
) -> Optional[Scene]:
    """Retrieves a scene, enforcing project ownership, including recommendations."""
    query = (
        select(Scene)
        .join(Project, Scene.project_id == Project.id)
        .where(
            Scene.id == scene_id,
            or_(Project.user_id == user_id, Project.user_id.is_(None)),
        )
        .options(selectinload(Scene.shot_recommendations))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_scene(
    db: AsyncSession, scene_id: int, user_id: uuid.UUID, data: SceneUpdate
) -> Optional[Scene]:
    """Updates a scene if the user owns the parent project."""
    scene = await get_scene_by_id(db, scene_id, user_id)
    if not scene:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scene, key, value)

    await db.commit()
    await db.refresh(scene)
    return scene


async def delete_scene(
    db: AsyncSession, scene_id: int, user_id: uuid.UUID
) -> bool:
    """Deletes a scene if the user owns the parent project."""
    query = (
        select(Scene.id)
        .join(Project, Scene.project_id == Project.id)
        .where(
            Scene.id == scene_id,
            or_(Project.user_id == user_id, Project.user_id.is_(None)),
        )
    )
    result = await db.execute(query)
    found_id = result.scalar_one_or_none()

    if not found_id:
        return False

    delete_query = delete(Scene).where(Scene.id == found_id)
    await db.execute(delete_query)
    await db.commit()
    return True
