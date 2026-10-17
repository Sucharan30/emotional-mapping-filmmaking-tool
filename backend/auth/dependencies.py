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

from auth.base import AuthUser, AuthenticationError
from auth.supabase_auth import SupabaseAuthProvider

_bearer = HTTPBearer(auto_error=False)

# Singleton — swap this to change providers without touching routers.
_auth_provider = SupabaseAuthProvider()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    """
    FastAPI dependency: extracts and verifies the Bearer token.
    Returns the authenticated user or raises HTTP 401.

    Note: ownership returns 404, not 403 — so the API does not
    reveal whether a resource exists at all (enforced in services).
    """
    if credentials is None:
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )
