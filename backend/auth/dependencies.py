"""
auth/dependencies.py — FastAPI dependency for authenticated routes.

Usage in a router:
    from auth.dependencies import get_current_user
    from auth.base import AuthUser

    @router.get("/me")
    async def me(user: AuthUser = Depends(get_current_user)):
        ...

To swap the auth provider, change _auth_provider below.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import uuid

from auth.base import AuthUser, AuthenticationError
from auth.supabase_auth import SupabaseAuthProvider
from config import settings

_bearer = HTTPBearer(auto_error=False)

# Singleton — swap this to change providers without touching routers.
_auth_provider = SupabaseAuthProvider()

# Default user for development testing (bypasses Supabase Email OTP)
DEV_USER = AuthUser(
    id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
    email="filmmaker@created.local",
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    """
    FastAPI dependency: extracts and verifies the Bearer token.
    - In dev mode (settings.auth_mode == 'dev') or if credentials are omitted:
      returns DEV_USER so all endpoints can be tested without email OTP.
    - In production/enforced mode: verifies token with Supabase or raises 401.
    """
    if credentials is None:
        if settings.auth_mode == "dev":
            return DEV_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "missing_token",
                "message": "Authentication required. Please sign in.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await _auth_provider.verify_token(credentials.credentials)
    except AuthenticationError as exc:
        if settings.auth_mode == "dev":
            return DEV_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )
