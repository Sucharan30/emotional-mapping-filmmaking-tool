"""
routers/meta.py — Metadata router.
"""

from fastapi import APIRouter

import constants
from schemas import MetaOptionsResponse

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/options", response_model=MetaOptionsResponse)
async def get_options():
    """
    Returns all valid dropdown options and enums used by the application.
    The frontend should use this to populate its UI dynamically.
    """
    return MetaOptionsResponse(
        emotions=constants.EMOTIONS,
        budget_levels=constants.BUDGET_LEVELS,
        character_focus_options=constants.CHARACTER_FOCUS_OPTIONS,
        complexity_levels=constants.COMPLEXITY_LEVELS,
        budget_fit_levels=constants.BUDGET_FIT_LEVELS,
        project_types=constants.PROJECT_TYPES,
        kb_categories=constants.KB_CATEGORIES,
        kb_review_status=constants.KB_REVIEW_STATUS,
    )
