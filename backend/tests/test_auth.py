"""
tests/test_auth.py — Authentication and token verification unit tests.
"""

import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from auth.base import AuthenticationError
from auth.dependencies import get_current_user
from auth.supabase_auth import SupabaseAuthProvider
from main import app


@pytest.mark.asyncio
async def test_auth_me_requires_token():
    """Unauthenticated request to protected endpoint returns HTTP 401."""
    # Ensure no dependency override for get_current_user
    app.dependency_overrides.pop(get_current_user, None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "missing_token"


@pytest.mark.asyncio
async def test_auth_me_invalid_token():
    """Invalid token returns HTTP 401 with invalid_token code."""
    app.dependency_overrides.pop(get_current_user, None)

    with patch.object(
        SupabaseAuthProvider, "verify_token", side_effect=AuthenticationError("Invalid or expired token.")
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer bad-token-xyz"}
            )

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "invalid_token"


@pytest.mark.asyncio
async def test_auth_me_valid_user():
    """Valid token returns current user ID and email."""
    test_user_id = uuid.uuid4()
    test_email = "director@cinema.com"

    # Mock Supabase Auth REST API returning 200 with user data
    mock_response = httpx.Response(
        status_code=200,
        json={"id": str(test_user_id), "email": test_email},
        request=httpx.Request("GET", "https://example.supabase.co/auth/v1/user")
    )

    provider = SupabaseAuthProvider()
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)):
        user = await provider.verify_token("valid-jwt-token-123")

    assert user.id == test_user_id
    assert user.email == test_email


@pytest.mark.asyncio
async def test_auth_service_timeout():
    """Supabase Auth service timeout maps to an AuthenticationError."""
    provider = SupabaseAuthProvider()
    with patch("httpx.AsyncClient.get", AsyncMock(side_effect=httpx.TimeoutException("Timeout"))):
        with pytest.raises(AuthenticationError) as exc_info:
            await provider.verify_token("test-timeout-token")

    assert "timed out" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_auth_service_network_error():
    """Supabase Auth unreachable maps to an AuthenticationError."""
    provider = SupabaseAuthProvider()
    with patch("httpx.AsyncClient.get", AsyncMock(side_effect=httpx.RequestError("Network down"))):
        with pytest.raises(AuthenticationError) as exc_info:
            await provider.verify_token("test-network-error-token")

    assert "could not reach" in exc_info.value.message.lower()
