"""
routers/auth.py — Authentication router.
"""

from fastapi import APIRouter, Depends

from auth import AuthUser, get_current_user
from schemas import AuthMeResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=AuthMeResponse)
async def get_me(user: AuthUser = Depends(get_current_user)):
    """
    Verifies the Bearer token and returns the current user's ID and email.
    Used by the frontend to confirm backend session state.
    """
    return AuthMeResponse(id=user.id, email=user.email)
