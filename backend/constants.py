"""
constants.py — Controlled vocabularies for the Emotional Mapping application.

All valid enum values live here. Change values in this one file;
the database CHECK constraints, Pydantic validators, and the
GET /api/v1/meta/options endpoint all read from here.
"""

from typing import List

# ── Emotions ──────────────────────────────────────────────────────────────────
# Used in:
#   - scenes.target_emotion
#   - knowledge_base.potential_emotions[] values
#   - GET /api/v1/meta/options
EMOTIONS: List[str] = [
    "empathy",
    "power",
    "vulnerability",
    "tension",
    "isolation",
    "intimacy",
    "detachment",
    "blame",
]

# ── Production budget levels ──────────────────────────────────────────────────
BUDGET_LEVELS: List[str] = ["low", "medium", "high"]

# ── Character focus options ───────────────────────────────────────────────────
CHARACTER_FOCUS_OPTIONS: List[str] = [
    "character_a",
    "character_b",
    "neutral_observer",
]

# ── Production complexity ─────────────────────────────────────────────────────
COMPLEXITY_LEVELS: List[str] = ["Low", "Medium", "High"]

# ── Budget fit ────────────────────────────────────────────────────────────────
BUDGET_FIT_LEVELS: List[str] = ["good_fit", "stretch", "beyond_budget"]

# ── Project types ─────────────────────────────────────────────────────────────
PROJECT_TYPES: List[str] = ["shot_design", "audience_test"]

# ── Knowledge base categories ─────────────────────────────────────────────────
KB_CATEGORIES: List[str] = ["angle", "shot_type", "framing", "movement", "distance"]

# ── Knowledge base review status ─────────────────────────────────────────────
KB_REVIEW_STATUS: List[str] = ["draft", "reviewed"]

# ── Film familiarity (for personas — implemented later) ───────────────────────
FILM_FAMILIARITY_OPTIONS: List[str] = ["Casual", "Regular", "Enthusiast"]

# ── LLM providers ────────────────────────────────────────────────────────────
LLM_PROVIDERS: List[str] = ["gemini"]

# ── Feature names for ai_usage tracking ──────────────────────────────────────
FEATURE_SHOT_DESIGNER = "shot_designer"
FEATURE_AUDIENCE_LENS = "audience_lens"  # future

# ── Field constraints ─────────────────────────────────────────────────────────
SCENE_DESCRIPTION_MIN_CHARS: int = 10
SCENE_DESCRIPTION_MAX_CHARS: int = 2000
BUDGET_NOTES_MAX_CHARS: int = 300
PROJECT_NAME_MAX_CHARS: int = 200

# ── Shot Designer constraints ─────────────────────────────────────────────────
SHOT_RECS_MIN: int = 4
SHOT_RECS_MAX: int = 5
CHECKLIST_ITEMS_MIN: int = 3
CHECKLIST_ITEMS_MAX: int = 6

# ── Knowledge base retrieval ──────────────────────────────────────────────────
KNOWLEDGE_BASE_RETRIEVAL_LIMIT: int = 12
KNOWLEDGE_BASE_MIN_MATCH: int = 8   # top up with category variety below this
