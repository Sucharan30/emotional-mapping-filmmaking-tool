"""
llm/mock_provider.py — Deterministic/realistic fallback LLM provider.
Used for offline development, integration testing, or when Google Gemini API
is temporarily undergoing high-demand outages.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Type

from llm.base import LLMProvider, LLMUsage, T
from schemas import (
    BudgetFit,
    LLMShotDesignerOutput,
    LLMShotRecommendation,
    ProductionComplexity,
)


class MockLLMProvider(LLMProvider):
    """
    Generates realistic, professional cinematography recommendations without external API calls.
    Extracts knowledge base IDs from the prompt to ensure realistic grounded outputs.
    """

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> Tuple[T, LLMUsage]:
        # Extract available Knowledge Base IDs from user prompt
        kb_id_matches = re.findall(r"ID:\s*(\w+)", user_prompt)
        kb_ids = kb_id_matches[:3] if kb_id_matches else []

        mock_output = LLMShotDesignerOutput(
            recommendations=[
                LLMShotRecommendation(
                    rank=1,
                    perspective_name="The Claustrophobic Observer (High-Angle Medium Close-Up)",
                    reasoning="Creates mounting psychological vulnerability by compressing the subject against the dark background, heightening perceived pressure.",
                    visual_checklist=[
                        "50mm prime lens at T2.0 for tight depth of field",
                        "Camera 25 degrees above subject eyeline tilted downward",
                        "Single overhead practical bare bulb key with 40-degree grid",
                        "Subtle handheld breathing motion to reflect character tension",
                        "Frame left-biased to create unbalanced negative headroom",
                    ],
                    context_caveat="Ensure fill light is completely flagged off to prevent reducing contrast ratio.",
                    production_complexity=ProductionComplexity(
                        level="Low",
                        reason="Standard prime lens with minimal grip gear; single diffused lamp.",
                    ),
                    budget_fit=BudgetFit(
                        level="good_fit",
                        reason="Operable within low/medium budget using standard tripod and basic package.",
                    ),
                    knowledge_base_ids=kb_ids[:1],
                ),
                LLMShotRecommendation(
                    rank=2,
                    perspective_name="Intimate Subjective Eye-Level Tracking",
                    reasoning="Forces direct emotional identification with the character's internal turmoil through confronting eye-level framing.",
                    visual_checklist=[
                        "35mm wide-normal lens positioned exactly at subject eyeline",
                        "Slow pushing push-in tracking movement toward the eyes",
                        "Edge rim light to separate subject silhouette from background",
                        "Shallow focal plane keeping only the eyes pin-sharp",
                        "Centered composition capturing subtle micro-expressions",
                    ],
                    context_caveat="Requires precise actor eyeline discipline and steady camera operator movement.",
                    production_complexity=ProductionComplexity(
                        level="Medium",
                        reason="Requires a stabilized slider or gentle gimbal push-in.",
                    ),
                    budget_fit=BudgetFit(
                        level="good_fit",
                        reason="Within medium production budget parameters with standard equipment.",
                    ),
                    knowledge_base_ids=kb_ids[1:2] if len(kb_ids) > 1 else kb_ids[:1],
                ),
                LLMShotRecommendation(
                    rank=3,
                    perspective_name="Oppressive Dutch-Angle Low Profile",
                    reasoning="Induces disorientation and impending narrative dread by breaking conventional horizon balance.",
                    visual_checklist=[
                        "24mm wide angle lens placed 18 inches above floor level",
                        "12-degree counter-clockwise Dutch tilt",
                        "Heavy shadow falloff across the unlit side of the face",
                        "Deep focus maintaining sharp background geometry and doorframe",
                    ],
                    context_caveat="Avoid excessive tilt angle which can feel melodramatic rather than grounded.",
                    production_complexity=ProductionComplexity(
                        level="Low",
                        reason="Easily achieved with low-hat mount or ground spreader tripod.",
                    ),
                    budget_fit=BudgetFit(
                        level="good_fit",
                        reason="Zero specialized gear required.",
                    ),
                    knowledge_base_ids=kb_ids[2:3] if len(kb_ids) > 2 else kb_ids[:1],
                ),
                LLMShotRecommendation(
                    rank=4,
                    perspective_name="Detached Silhouette Through-Frame Tableau",
                    reasoning="Emphasizes alienation and helplessness by placing the character as an isolated silhouette within an overwhelming void.",
                    visual_checklist=[
                        "85mm telephoto lens from across the room",
                        "Backlit subject creating sharp contour silhouette",
                        "Static locked-off camera position for observational distance",
                        "Subtle practical flicker timed with scene climax",
                    ],
                    context_caveat="Relies heavily on lighting contrast; actor facial expressions will be obscured.",
                    production_complexity=ProductionComplexity(
                        level="Medium",
                        reason="Requires deliberate lighting placement and long focal throw.",
                    ),
                    budget_fit=BudgetFit(
                        level="good_fit",
                        reason="Standard lighting stands and telephoto lens.",
                    ),
                    knowledge_base_ids=kb_ids[:2],
                ),
            ]
        )

        usage = LLMUsage(
            input_tokens=850,
            output_tokens=620,
            model="mock-cinematographer-v1",
        )

        return mock_output, usage
