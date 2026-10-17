"""
tests/test_api_behavior.py — General API behavior, CORS, validation errors, and metadata.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Health check returns 200 with status ok."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data


@pytest.mark.asyncio
async def test_api_v1_health_check(async_client: AsyncClient):
    """Versioned health check under /api/v1/health returns 200."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_meta_options_returns_controlled_vocabularies(async_client: AsyncClient):
    """Meta options returns emotions, budget tiers, and complexity options."""
    response = await async_client.get("/api/v1/meta/options")
    assert response.status_code == 200
    data = response.json()
    assert "emotions" in data
    assert "empathy" in data["emotions"]
    assert "power" in data["emotions"]
    assert "budget_levels" in data
    assert "low" in data["budget_levels"]
    assert "complexity_levels" in data
    assert "Low" in data["complexity_levels"]
    assert "kb_categories" in data
    assert "kb_review_status" in data


@pytest.mark.asyncio
async def test_request_validation_error_format(async_client: AsyncClient):
    """Pydantic validation failure returns HTTP 422 with uniform error envelope."""
    # Send empty body where project_id & description are required
    response = await async_client.post("/api/v1/scenes", json={})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "validation_error"
    assert "message" in data["error"]
    assert "details" in data["error"]


@pytest.mark.asyncio
async def test_cors_preflight(async_client: AsyncClient):
    """CORS preflight request returns allowed origin and methods."""
    response = await async_client.options(
        "/api/v1/meta/options",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
