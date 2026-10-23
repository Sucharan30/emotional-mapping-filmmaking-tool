"""
tests/conftest.py — Test fixtures and configuration.
All tests use mocks/fakes and DO NOT connect to live Supabase or Gemini.
"""

from __future__ import annotations

import os
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Explicit test defaults so tests never depend on local .env presence
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://mock:mock@localhost:5432/mock")
os.environ.setdefault("SUPABASE_URL", "https://mock.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "mock-anon-key")
os.environ.setdefault("GEMINI_API_KEY", "mock-gemini-key")
os.environ.setdefault("AUTH_MODE", "dev")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from auth.base import AuthUser
from auth.dependencies import get_current_user
from db import get_db
from llm.base import LLMProvider, LLMUsage
from llm import get_llm
from main import app
from schemas import (
    BudgetFit,
    LLMShotDesignerOutput,
    LLMShotRecommendation,
    ProductionComplexity,
)

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TEST_USER = AuthUser(id=TEST_USER_ID, email="filmmaker@example.com")
OTHER_USER = AuthUser(id=OTHER_USER_ID, email="intruder@example.com")


class FakeLLMProvider(LLMProvider):
    """Configurable fake LLM provider for unit tests without hitting Gemini."""

    def __init__(self, output: LLMShotDesignerOutput | None = None, should_fail: Exception | None = None):
        self.should_fail = should_fail
        self.call_count = 0
        if output is None:
            self.output = LLMShotDesignerOutput(
                recommendations=[
                    LLMShotRecommendation(
                        rank=1,
                        perspective_name="Intimate High-Angle POV",
                        reasoning="Creates emotional vulnerability while maintaining character identification.",
                        visual_checklist=[
                            "50mm prime lens at T2.0",
                            "Camera positioned 30 degrees above subject eyeline",
                            "Slight slow handheld breathing motion",
                            "Key light diffused from camera left",
                        ],
                        context_caveat="Can feel artificial if the angle is too steep.",
                        production_complexity=ProductionComplexity(
                            level="Low",
                            reason="Requires standard tripod or shoulder rig with no specialized grip."
                        ),
                        budget_fit=BudgetFit(
                            level="good_fit",
                            reason="Easily achieved with standard camera package."
                        ),
                        knowledge_base_ids=[],
                    ),
                    LLMShotRecommendation(
                        rank=2,
                        perspective_name="Objective Wide Tracking",
                        reasoning="Emphasizes spatial isolation within the environment.",
                        visual_checklist=[
                            "24mm wide angle lens",
                            "Waist-level camera tracking parallel to subject",
                            "Deep depth of field at T5.6",
                            "Maintain wide headroom to stress architecture",
                        ],
                        context_caveat="Reduces facial micro-expression readability.",
                        production_complexity=ProductionComplexity(
                            level="Medium",
                            reason="Requires a smooth motorized slider or floor dolly track."
                        ),
                        budget_fit=BudgetFit(
                            level="stretch",
                            reason="Requires a track or stabilizer gimbal on smaller budgets."
                        ),
                        knowledge_base_ids=[],
                    ),
                    LLMShotRecommendation(
                        rank=3,
                        perspective_name="Dutch Angle Medium Close-Up",
                        reasoning="Disorients viewer to reflect protagonist psychological panic.",
                        visual_checklist=[
                            "35mm lens, 12-degree roll tilt clockwise",
                            "Tight chest-up framing",
                            "High contrast rim lighting",
                        ],
                        context_caveat="Overuse can read as melodramatic.",
                        production_complexity=ProductionComplexity(
                            level="Low",
                            reason="Adjust tripod pan/tilt head directly."
                        ),
                        budget_fit=BudgetFit(
                            level="good_fit",
                            reason="No additional gear required."
                        ),
                        knowledge_base_ids=[],
                    ),
                    LLMShotRecommendation(
                        rank=4,
                        perspective_name="Slow Push-In to Extreme Close-Up",
                        reasoning="Gradually ratchets tension by eliminating peripheral escapes.",
                        visual_checklist=[
                            "85mm portrait telephoto lens",
                            "Smooth creeping push-in over 12 seconds",
                            "Focus pull tracking pupil",
                        ],
                        context_caveat="Requires precise focus puller rehearsal.",
                        production_complexity=ProductionComplexity(
                            level="Medium",
                            reason="Requires slider or meticulous dolly move."
                        ),
                        budget_fit=BudgetFit(
                            level="good_fit",
                            reason="Affordable on basic slider gear."
                        ),
                        knowledge_base_ids=[],
                    ),
                ]
            )
        else:
            self.output = output

    async def generate_structured(self, system_prompt, user_prompt, response_model):
        self.call_count += 1
        if self.should_fail:
            raise self.should_fail
        return self.output, LLMUsage(input_tokens=150, output_tokens=320, model="gemini-mock")


@pytest.fixture
def fake_llm():
    return FakeLLMProvider()


@pytest.fixture
def mock_db_session():
    """Mock async SQLAlchemy session."""
    session = AsyncMock(spec=AsyncSession)
    session.scalar = AsyncMock(return_value=0)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest_asyncio.fixture
async def async_client(mock_db_session, fake_llm) -> AsyncGenerator[AsyncClient, None]:
    """Test client with mock authentication and mock DB dependencies overridden."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_llm] = lambda: fake_llm

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
