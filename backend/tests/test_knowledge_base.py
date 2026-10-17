"""
tests/test_knowledge_base.py — Knowledge base API and service unit tests.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from models import KnowledgeBase


def make_kb_item(
    name: str = "Low Angle",
    category: str = "angle",
    emotions: list[str] | None = None,
    review_status: str = "reviewed",
) -> KnowledgeBase:
    return KnowledgeBase(
        id=uuid.uuid4(),
        technique_name=name,
        category=category,
        visual_characteristic="Camera positioned below subject eye line pointing up.",
        potential_emotions=emotions or ["power", "tension"],
        context_note="Contextual notes on power dynamics.",
        example_scene="A courtroom authority figure.",
        equipment_needs="Standard tripod.",
        typical_complexity="Low",
        review_status=review_status,
        source_note="Film analysis textbook chapter 4.",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_list_knowledge_base(async_client: AsyncClient):
    """Listing knowledge base returns paginated items and total count."""
    items = [make_kb_item("Low Angle"), make_kb_item("High Angle")]

    with patch("services.knowledge_base.list_knowledge_base_items", AsyncMock(return_value=(items, 2))):
        response = await async_client.get("/api/v1/knowledge-base?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["technique_name"] == "Low Angle"
    assert data["items"][0]["source_note"] == "Film analysis textbook chapter 4."


@pytest.mark.asyncio
async def test_filter_knowledge_base_by_category(async_client: AsyncClient):
    """Filter by category works with valid category."""
    items = [make_kb_item("Dutch Angle", category="angle")]

    with patch("services.knowledge_base.list_knowledge_base_items", AsyncMock(return_value=(items, 1))):
        response = await async_client.get("/api/v1/knowledge-base?category=angle")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_filter_knowledge_base_invalid_category(async_client: AsyncClient):
    """Invalid category filter returns HTTP 400 with invalid_filter code."""
    response = await async_client.get("/api/v1/knowledge-base?category=invalid_cat_xyz")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "invalid_filter"


@pytest.mark.asyncio
async def test_filter_knowledge_base_invalid_emotion(async_client: AsyncClient):
    """Invalid emotion filter returns HTTP 400."""
    response = await async_client.get("/api/v1/knowledge-base?emotion=ecstasy")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "invalid_filter"


@pytest.mark.asyncio
async def test_get_knowledge_base_by_id_found(async_client: AsyncClient):
    """Existing technique returns 200 with full data."""
    item = make_kb_item("Slow Push-In", category="movement")

    with patch("services.knowledge_base.get_kb_item_by_id", AsyncMock(return_value=item)):
        response = await async_client.get(f"/api/v1/knowledge-base/{item.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["technique_name"] == "Slow Push-In"
    assert data["category"] == "movement"


@pytest.mark.asyncio
async def test_get_knowledge_base_by_id_not_found(async_client: AsyncClient):
    """Non-existent technique ID returns HTTP 404."""
    with patch("services.knowledge_base.get_kb_item_by_id", AsyncMock(return_value=None)):
        response = await async_client.get(f"/api/v1/knowledge-base/{uuid.uuid4()}")

    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "not_found"
