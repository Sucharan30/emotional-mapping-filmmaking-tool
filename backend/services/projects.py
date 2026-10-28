"""
services/projects.py — Project lifecycle management.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from models import Project
from schemas import ProjectCreate, ProjectUpdate


async def create_project(
    db: AsyncSession, user_id: uuid.UUID, data: ProjectCreate
) -> Project:
    now = datetime.now(timezone.utc)
    # In dev mode or for mock DEV_USER (all zeros), user_id does not exist in auth.users,
    # so we store None (nullable foreign key) to satisfy PostgreSQL constraint.
    db_user_id = (
        None
        if (settings.auth_mode == "dev" or str(user_id) == "00000000-0000-0000-0000-000000000000")
        else user_id
    )
    project = Project(
        user_id=db_user_id,
        name=data.name,
        type=data.type,
        description=data.description,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    try:
        await db.commit()
    except Exception as e:
        if "projects_user_id_fkey" in str(e):
            await db.rollback()
            project.user_id = None
            db.add(project)
            await db.commit()
        else:
            raise
    await db.refresh(project)
    return project


async def get_projects_for_user(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> tuple[Sequence[Project], int]:
    # Total count including legacy/unassigned records in dev testing
    count_query = select(func.count(Project.id)).where(
        or_(Project.user_id == user_id, Project.user_id.is_(None))
    )
    total = await db.scalar(count_query) or 0

    # Items
    query = (
        select(Project)
        .where(or_(Project.user_id == user_id, Project.user_id.is_(None)))
        .options(selectinload(Project.scenes))
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_project_by_id(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Project]:
    query = (
        select(Project)
        .where(
            Project.id == project_id,
            or_(Project.user_id == user_id, Project.user_id.is_(None)),
        )
        .options(selectinload(Project.scenes))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, data: ProjectUpdate
) -> Optional[Project]:
    project = await get_project_by_id(db, project_id, user_id)
    if not project:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    project.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    query = delete(Project).where(
        Project.id == project_id,
        or_(Project.user_id == user_id, Project.user_id.is_(None)),
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0
