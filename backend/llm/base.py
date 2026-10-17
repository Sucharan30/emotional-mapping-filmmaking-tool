"""
llm/base.py — Abstract interface for LLM providers.

To add a new LLM provider (e.g., OpenAI, Claude, Ollama):
  1. Create a new file in llm/, e.g. llm/openai.py
  2. Implement LLMProvider
  3. Add one case to get_llm() in llm/__init__.py
  4. Set LLM_PROVIDER=openai in .env
No changes needed in services or routers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Tuple, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMUsage:
    """Token usage and model info from one LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class LLMError(Exception):
    """
    The LLM returned an error: timeout, quota exceeded, network failure,
    or any non-validation error.
    """
    def __init__(self, message: str = "The AI service returned an error.") -> None:
        super().__init__(message)
        self.message = message


class LLMValidationError(Exception):
    """
    The LLM returned a response that could not be validated against the
    expected schema, even after one automatic retry with a repair instruction.
    The API maps this to HTTP 502 with a user-safe message.
    """
    def __init__(
        self,
        message: str = (
            "The AI response could not be understood. "
            "Please try again or rephrase your scene description."
        ),
    ) -> None:
        super().__init__(message)
        self.message = message


class LLMProvider(ABC):
    """
    Interface all LLM providers must implement.
    Services import and use only this interface — never a vendor SDK.
    """

    @abstractmethod
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> Tuple[T, LLMUsage]:
        """
        Generate a structured response conforming to response_model.

        Args:
            system_prompt:  Role and constraints for the model.
            user_prompt:    The request content and context.
            response_model: A Pydantic model class. The LLM output must
                            validate against this model.

        Returns:
            (parsed_instance, usage)

        Raises:
            LLMError:           Timeout, quota, or network failure.
            LLMValidationError: Could not produce valid output after retry.
        """
        raise NotImplementedError
