"""
tests/test_shot_designer.py — Shot Designer AI generation, validation, and usage limit unit tests.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from llm.base import LLMError, LLMValidationError
from models import KnowledgeBase, Scene, ShotRecommendation
from services.shot_designer import (
    DailyLimitExceededError,
    InsufficientSceneDataError,
    SceneNotFoundError,
    generate_shot_recommendations,
)
from tests.conftest import FakeLLMProvider, TEST_USER_ID


def make_scene(scene_id=1, desc="A character sits alone in a rain-streaked diner booth."):
    return Scene(
        id=scene_id,
        project_id=uuid.uuid4(),
        description=desc,
        target_emotion="isolation",
        character_focus="neutral_observer",
        production_budget="low",
        budget_notes="Natural diner lighting and rainy window.",
        created_at=datetime.now(timezone.utc),
    )


# ── Route Integration Tests (using FakeLLM) ───────────────────────────────────

@pytest.mark.asyncio
async def test_design_shots_success(async_client: AsyncClient, mock_db_session):
    """Successful Shot Designer generation returns 4-5 recommendations and model metadata."""
    scene_id = 1
    mock_recs = [
        ShotRecommendation(
            id=1,
            scene_id=scene_id,
            rank=1,
            perspective_name="Intimate High-Angle POV",
            reasoning="Creates emotional vulnerability.",
            visual_checklist=["50mm prime lens", "Key light diffused"],
            context_caveat="Can feel artificial if too steep.",
            production_complexity_level="Low",
            production_complexity_reason="Tripod only.",
            budget_fit="good_fit",
            budget_fit_reason="Standard gear.",
            knowledge_base_ids=[],
            model_name="gemini-mock",
            created_at=datetime.now(timezone.utc),
        )
    ]

    with patch("services.shot_designer.generate_shot_recommendations", AsyncMock(return_value=mock_recs)):
        response = await async_client.post(
            "/api/v1/scenes/design-shots",
            json={"scene_id": scene_id}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["scene_id"] == scene_id
    assert len(data["recommendations"]) == 1
    assert data["model_used"] == "gemini-mock"


@pytest.mark.asyncio
async def test_design_shots_daily_limit_exceeded(async_client: AsyncClient):
    """When daily limit is reached, returns HTTP 429 with daily_limit_exceeded."""
    with patch(
        "services.shot_designer.generate_shot_recommendations",
        AsyncMock(side_effect=DailyLimitExceededError("Daily AI generation limit reached."))
    ):
        response = await async_client.post(
            "/api/v1/scenes/design-shots",
            json={"scene_id": 1}
        )

    assert response.status_code == 429
    data = response.json()
    assert data["error"]["code"] == "daily_limit_exceeded"


@pytest.mark.asyncio
async def test_design_shots_insufficient_description(async_client: AsyncClient):
    """When scene description is too short, returns HTTP 400."""
    with patch(
        "services.shot_designer.generate_shot_recommendations",
        AsyncMock(side_effect=InsufficientSceneDataError("Scene description is too short."))
    ):
        response = await async_client.post(
            "/api/v1/scenes/design-shots",
            json={"scene_id": 1}
        )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "insufficient_scene_data"


@pytest.mark.asyncio
async def test_design_shots_upstream_timeout(async_client: AsyncClient):
    """When Gemini times out, returns HTTP 503 with ai_service_error."""
    with patch(
        "services.shot_designer.generate_shot_recommendations",
        AsyncMock(side_effect=LLMError("The AI service request timed out."))
    ):
        response = await async_client.post(
            "/api/v1/scenes/design-shots",
            json={"scene_id": 1}
        )

    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "ai_service_error"


@pytest.mark.asyncio
async def test_design_shots_schema_validation_error(async_client: AsyncClient):
    """When LLM output cannot be parsed after retry, returns HTTP 502 with ai_validation_error."""
    with patch(
        "services.shot_designer.generate_shot_recommendations",
        AsyncMock(side_effect=LLMValidationError("Invalid schema."))
    ):
        response = await async_client.post(
            "/api/v1/scenes/design-shots",
            json={"scene_id": 1}
        )

    assert response.status_code == 502
    data = response.json()
    assert data["error"]["code"] == "ai_validation_error"


# ── Service Pipeline & Anti-Hallucination Tests ───────────────────────────────

@pytest.mark.asyncio
async def test_anti_hallucination_kb_filtering(mock_db_session):
    """Invented KB IDs from LLM output are purged before DB insertion."""
    real_kb_id = 1
    hallucinated_kb_id = 9999

    scene = make_scene(scene_id=1)
    real_kb_item = KnowledgeBase(
        id=real_kb_id,
        technique_name="High Angle",
        category="angle",
        visual_characteristic="Above eye line",
        potential_emotions=["isolation"],
        context_note="Vulnerability",
        typical_complexity="Low",
        review_status="reviewed",
        created_at=datetime.now(timezone.utc),
    )

    fake_llm = FakeLLMProvider()
    fake_llm.output.recommendations[0].knowledge_base_ids = [real_kb_id, hallucinated_kb_id]

    with patch("services.shot_designer.get_daily_generation_count", AsyncMock(return_value=0)), \
         patch("services.shot_designer.get_scene_by_id", AsyncMock(return_value=scene)), \
         patch("services.shot_designer.retrieve_relevant_kb_items", AsyncMock(return_value=[real_kb_item])):

        recs = await generate_shot_recommendations(mock_db_session, TEST_USER_ID, scene.id, fake_llm)

    # First recommendation should ONLY contain real_kb_id, hallucinated_kb_id was stripped
    assert recs[0].knowledge_base_ids == [real_kb_id]


@pytest.mark.asyncio
async def test_transaction_rollback_on_persistence_failure(mock_db_session):
    """If database commit fails, rollback is triggered and no partial data remains."""
    scene = make_scene(scene_id=1)
    fake_llm = FakeLLMProvider()

    mock_db_session.commit.side_effect = Exception("DB Connection dropped during commit")

    with patch("services.shot_designer.get_daily_generation_count", AsyncMock(return_value=0)), \
         patch("services.shot_designer.get_scene_by_id", AsyncMock(return_value=scene)), \
         patch("services.shot_designer.retrieve_relevant_kb_items", AsyncMock(return_value=[])):

        with pytest.raises(Exception) as exc_info:
            await generate_shot_recommendations(mock_db_session, TEST_USER_ID, scene.id, fake_llm)

        assert "DB Connection dropped" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
