"""
llm/gemini_provider.py — Google Gemini implementation of LLMProvider.

Uses the official google-genai SDK.
Handles:
  - Validating output against a Pydantic schema using response_schema.
  - One automatic retry on validation failure with an appended
    correction prompt.
  - Tracking tokens accurately from usage_metadata.
  - Handling rate limits, auth errors, and timeouts safely.

Configuration comes directly from config.py.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Tuple, Type

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError

from config import settings
from llm.base import LLMError, LLMProvider, LLMUsage, LLMValidationError, T

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Implements LLMProvider using the google-genai SDK.
    Always produces output matching the provided Pydantic schema.
    """

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model
        self._thinking_budget = settings.thinking_budget
        self._timeout_seconds = settings.llm_timeout_seconds

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> Tuple[T, LLMUsage]:
        """
        Calls Gemini, requesting JSON matching `response_model`.
        If the schema validation fails, retries once with the error detail.
        """
        return await self._call_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=response_model,
            retries_left=1,
        )

    async def _call_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        retries_left: int,
    ) -> Tuple[T, LLMUsage]:
        config_kwargs = {
            "system_instruction": system_prompt,
            "response_mime_type": "application/json",
            "response_schema": response_model,
            "temperature": 0.7,
        }

        # Safe optional thinking budget
        if self._thinking_budget > 0 and hasattr(types, "ThinkingConfig"):
            try:
                config_kwargs["thinking_config"] = types.ThinkingConfig(
                    thinking_budget=self._thinking_budget
                )
            except Exception as e:
                logger.warning("ThinkingConfig skipped due to compatibility: %s", e)

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._model,
                    contents=user_prompt,
                    config=config,
                ),
                timeout=float(self._timeout_seconds),
            )
        except asyncio.TimeoutError:
            logger.error("Gemini API call timed out after %s seconds", self._timeout_seconds)
            raise LLMError("The AI service request timed out. Please try again.")
        except APIError as exc:
            logger.error("Gemini API error: %s (status=%s)", exc, getattr(exc, "code", None))
            err_str = str(exc).lower()
            code = getattr(exc, "code", None)
            if code == 429 or "quota" in err_str or "resource_exhausted" in err_str:
                raise LLMError("AI rate limit or quota exceeded. Please try again later.")
            if code in (401, 403) or "unauthenticated" in err_str or "permission" in err_str:
                raise LLMError("AI service authentication failed. Check your Gemini API key.")
            raise LLMError("The AI service is currently unavailable.")
        except Exception as exc:
            if isinstance(exc, (LLMError, LLMValidationError)):
                raise
            logger.error("Unexpected error in Gemini generation: %s", exc)
            raise LLMError("An unexpected error occurred while communicating with the AI service.")

        usage = LLMUsage(
            input_tokens=0,
            output_tokens=0,
            model=self._model,
        )

        if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
            usage.input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            usage.output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

        raw_text = getattr(response, "text", None)
        if not raw_text or not raw_text.strip():
            if retries_left > 0:
                logger.warning("Empty response from Gemini. Retrying once...")
                return await self._call_with_retry(
                    system_prompt,
                    user_prompt + "\n\nCRITICAL: You must provide a non-empty JSON response conforming to the schema.",
                    response_model,
                    retries_left - 1,
                )
            raise LLMValidationError("The AI provided an empty response.")

        try:
            parsed_instance = response_model.model_validate_json(raw_text)
            return parsed_instance, usage
        except ValidationError as validation_err:
            logger.warning("Gemini output schema validation failed. Retries left: %s", retries_left)
            logger.warning("Raw response was: %s", raw_text)

            if retries_left > 0:
                correction_prompt = (
                    f"{user_prompt}\n\n"
                    f"CRITICAL FIX REQUIRED: Your previous output failed schema validation.\n"
                    f"Validation errors:\n{validation_err}\n\n"
                    f"Correct the JSON and return valid JSON conforming strictly to the requested schema."
                )
                return await self._call_with_retry(
                    system_prompt,
                    correction_prompt,
                    response_model,
                    retries_left - 1,
                )

            raise LLMValidationError(
                "The AI response could not be validated against the expected format. Please try again."
            )
