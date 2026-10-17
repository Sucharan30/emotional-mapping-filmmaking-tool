"""
auth/supabase_auth.py — Supabase implementation of AuthProvider.

Verifies access tokens by calling the Supabase Auth REST API:
  GET {SUPABASE_URL}/auth/v1/user
  Headers:
    Authorization: Bearer <token>
    apikey: <SUPABASE_ANON_KEY>

This approach is independent of the JWT signing method configured
in Supabase (HS256 or RS256) and works transparently.

Caching:
  Successful verifications are cached in memory for 60 seconds,
  keyed by a SHA-256 hash of the token. This avoids calling
  Supabase on every single request while keeping the cache safe
  (the raw token is never stored).
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from typing import Dict, Tuple

import httpx

from auth.base import AuthProvider, AuthUser, AuthenticationError
from config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache: {token_hash: (AuthUser, expiry_monotonic)}
_cache: Dict[str, Tuple[AuthUser, float]] = {}
_CACHE_TTL_SECONDS: float = 60.0


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _get_cached(token: str) -> AuthUser | None:
    key = _hash_token(token)
    entry = _cache.get(key)
    if entry is None:
        return None
    user, expiry = entry
    if time.monotonic() > expiry:
        _cache.pop(key, None)
        return None
    return user


def _set_cache(token: str, user: AuthUser) -> None:
    key = _hash_token(token)
    _cache[key] = (user, time.monotonic() + _CACHE_TTL_SECONDS)


class SupabaseAuthProvider(AuthProvider):
    """Verifies tokens against the Supabase Auth REST API."""

    def __init__(self) -> None:
        self._user_url = f"{settings.supabase_url}/auth/v1/user"
        self._anon_key = settings.supabase_anon_key

    async def verify_token(self, token: str) -> AuthUser:
        cached = _get_cached(token)
        if cached is not None:
            return cached

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self._user_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "apikey": self._anon_key,
                    },
                )
        except httpx.TimeoutException:
            logger.warning("Supabase auth check timed out")
            raise AuthenticationError(
                "Authentication service timed out. Please try again."
            )
        except httpx.RequestError as exc:
            logger.error("Supabase auth request error: %s", exc)
            raise AuthenticationError(
                "Could not reach the authentication service."
            )

        if response.status_code == 200:
            data = response.json()
            user = AuthUser(
                id=uuid.UUID(data["id"]),
                email=data["email"],
            )
            _set_cache(token, user)
            return user

        if response.status_code in (401, 403):
            raise AuthenticationError()

        logger.error(
            "Unexpected Supabase auth response: %s — %s",
            response.status_code,
            response.text[:200],
        )
        raise AuthenticationError("Authentication check failed unexpectedly.")
