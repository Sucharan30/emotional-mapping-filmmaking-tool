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
import copy
import logging
from typing import Any, Dict, Tuple, Type

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, ValidationError

from config import settings
from llm.base import LLMError, LLMProvider, LLMUsage, LLMValidationError, T

logger = logging.getLogger(__name__)


def _to_gemini_schema(model_or_schema: Any) -> Dict[str, Any]:
    """
    Converts a Pydantic model to a clean, fully inlined OpenAPI 3.0 schema dictionary
    compatible with the google-genai SDK.

    The google-genai SDK's types.Schema rejects '$defs' and '$ref' pointers when validating
    Pydantic schemas. This helper inlines all definitions recursively and converts types
    to uppercase strings expected by Gemini.
    """
    if isinstance(model_or_schema, dict):
        return model_or_schema

    if not hasattr(model_or_schema, "model_json_schema"):
        return model_or_schema

    raw_schema = model_or_schema.model_json_schema()
    defs = raw_schema.pop("$defs", {})

    def _resolve(node: Any) -> Any:
        if isinstance(node, dict):
            # Resolve all $ref occurrences by inlining from defs
            while "$ref" in node:
                ref_key = node.pop("$ref").split("/")[-1]
                if ref_key in defs:
                    target = copy.deepcopy(defs[ref_key])
                    target.pop("$defs", None)
                    node = {**target, **node}
                else:
                    break

            # Strip metadata fields that google-genai Schema rejects
            node.pop("title", None)
            node.pop("$defs", None)
            node.pop("default", None)

            # Uppercase types for Gemini OpenAPI spec
            if "type" in node and isinstance(node["type"], str):
                node["type"] = node["type"].upper()

            # Ensure ARRAY items are properly typed
            if node.get("type") == "ARRAY":
                if "items" not in node or not node["items"]:
                    node["items"] = {"type": "STRING"}
                elif (
                    isinstance(node["items"], dict)
                    and "type" not in node["items"]
                    and "$ref" not in node["items"]
                ):
                    node["items"]["type"] = "STRING"

            # Recurse through all dictionary values
            for k in list(node.keys()):
                node[k] = _resolve(node[k])

            return node
        elif isinstance(node, list):
            return [_resolve(item) for item in node]
        return node

    return _resolve(raw_schema)


class GeminiProvider(LLMProvider):
    """
    Implements LLMProvider using the google-genai SDK.
    Always produces output matching the provided Pydantic schema.
    """

    def __init__(self) -> None:
        self._model = settings.gemini_model
        self._thinking_budget = settings.thinking_budget
        self._timeout_seconds = settings.llm_timeout_seconds
        self._client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={"timeout": float(self._timeout_seconds)},
        )

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
            retries_left=3,
        )

    def _discover_best_model(self) -> str:
        """
        Dynamically queries Google GenAI for all models available to this API key
        and picks the best supported Flash model.
        """
        try:
            available = []
            for m in self._client.models.list():
                name = m.name.replace("models/", "")
                available.append(name)
            logger.info("Available Gemini models for your API key: %s", available)
            # Find first flash model or first supported model
            for candidate in available:
                if "flash" in candidate.lower() and "embed" not in candidate.lower():
                    return candidate
            if available:
                return available[0]
        except Exception as e:
            logger.warning("Could not automatically list models: %s", e)
        return self._model

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
            "response_schema": _to_gemini_schema(response_model),
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
            # Use asyncio.to_thread with synchronous generate_content to eliminate
            # Windows asyncio socket hangs and IOCP half-open stalls
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model=self._model,
                    contents=user_prompt,
                    config=config,
                ),
                timeout=float(self._timeout_seconds),
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Gemini API call timed out after %s seconds with model %s. Retries left: %s",
                self._timeout_seconds,
                self._model,
                retries_left,
            )
            if retries_left > 0:
                discovered = await asyncio.to_thread(self._discover_best_model)
                if discovered and discovered != self._model:
                    self._model = discovered
                    logger.info("Switching to discovered model: %s", self._model)
                await asyncio.sleep(2)
                return await self._call_with_retry(
                    system_prompt,
                    user_prompt,
                    response_model,
                    retries_left - 1,
                )
            raise LLMError("The AI service request timed out. Please try again.")
        except APIError as exc:
            logger.error("Gemini API error: %s (status=%s)", exc, getattr(exc, "code", None))
            err_str = str(exc).lower()
            code = getattr(exc, "code", None)

            # Auto-handle model deprecation / 404 or 503 high demand with auto-discovery
            if code in (404, 503) or "not_found" in err_str or "unavailable" in err_str:
                if retries_left > 0:
                    discovered = await asyncio.to_thread(self._discover_best_model)
                    if discovered and discovered != self._model:
                        self._model = discovered
                        logger.info("Switching to discovered model: %s", self._model)
                    delay = 3
                    logger.warning("Retrying with model %s in %ds...", self._model, delay)
                    await asyncio.sleep(delay)
                    return await self._call_with_retry(
                        system_prompt, user_prompt, response_model, retries_left - 1
                    )
                raise LLMError("The AI service is currently unavailable or high demand. Please try again later.")

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
