"""
tests/test_projects_scenes.py — Project & Scene CRUD and strict ownership enforcement.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from models import Project, Scene
from tests.conftest import OTHER_USER_ID, TEST_USER_ID


def make_project(user_id=TEST_USER_ID, name="Thriller Feature"):
    return Project(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        type="shot_design",
        description="A dark psychological feature.",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_scene(project_id, description="Detective confronts suspect in dimly lit interrogation room."):
    return Scene(
        id=uuid.uuid4(),
        project_id=project_id,
        description=description,
        target_emotion="tension",
        character_focus="character_a",
        production_budget="medium",
        budget_notes="Studio interior with two practical lamps.",
        created_at=datetime.now(timezone.utc),
    )


# ── Projects Tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_project(async_client: AsyncClient):
    """Authenticated user creates a new project."""
    project = make_project()
    with patch("services.projects.create_project", AsyncMock(return_value=project)):
        response = await async_client.post(
            "/api/v1/projects",
            json={"name": "Indie Noir", "type": "shot_design", "description": "Low-light indie."}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == project.name
    assert data["user_id"] == str(TEST_USER_ID)


@pytest.mark.asyncio
async def test_get_project_ownership_isolation(async_client: AsyncClient):
    """User cannot access another user's project (returns 404 to avoid ID leakage)."""
    # Service returns None because user_id does not match
    with patch("services.projects.get_project_by_id", AsyncMock(return_value=None)):
        response = await async_client.get(f"/api/v1/projects/{uuid.uuid4()}")

    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "project_not_found"


@pytest.mark.asyncio
async def test_delete_project_ownership_isolation(async_client: AsyncClient):
    """User cannot delete another user's project (returns 404)."""
    with patch("services.projects.delete_project", AsyncMock(return_value=False)):
        response = await async_client.delete(f"/api/v1/projects/{uuid.uuid4()}")

    assert response.status_code == 404


# ── Scenes Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_scene_success(async_client: AsyncClient):
    """User creates scene under their own project."""
    project = make_project()
    scene = make_scene(project.id)

    with patch("services.scenes.create_scene", AsyncMock(return_value=scene)):
        response = await async_client.post(
            "/api/v1/scenes",
            json={
                "project_id": str(project.id),
                "description": "Detective confronts suspect in dimly lit interrogation room.",
                "target_emotion": "tension",
                "character_focus": "character_a",
                "production_budget": "medium",
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert data["target_emotion"] == "tension"


@pytest.mark.asyncio
async def test_create_scene_unauthorized_project(async_client: AsyncClient):
    """User cannot create a scene under a project they do not own."""
    with patch(
        "services.scenes.create_scene",
        AsyncMock(side_effect=ValueError("Project not found or access denied"))
    ):
        response = await async_client.post(
            "/api/v1/scenes",
            json={
                "project_id": str(uuid.uuid4()),
                "description": "Attempting to hijack someone else's project scene.",
            }
        )

    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "project_not_found"


@pytest.mark.asyncio
async def test_get_scene_ownership_isolation(async_client: AsyncClient):
    """User cannot access another user's scene (returns 404)."""
    with patch("services.scenes.get_scene_by_id", AsyncMock(return_value=None)):
        response = await async_client.get(f"/api/v1/scenes/{uuid.uuid4()}")

    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "scene_not_found"


@pytest.mark.asyncio
async def test_get_scene_recommendations_ownership_isolation(async_client: AsyncClient):
    """User cannot retrieve recommendations for another user's scene."""
    with patch("services.scenes.get_scene_by_id", AsyncMock(return_value=None)):
        response = await async_client.get(f"/api/v1/scenes/{uuid.uuid4()}/recommendations")

    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "scene_not_found"
