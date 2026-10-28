"""
llm/__init__.py — LLM package initialization.

Provides a factory function `get_llm()` that returns the
configured LLMProvider based on the `.env` setting.
"""

from llm.base import LLMError, LLMProvider, LLMUsage, LLMValidationError
from llm.gemini_provider import GeminiProvider
from llm.mock_provider import MockLLMProvider
from config import settings


def get_llm() -> LLMProvider:
    """
    Returns the configured LLMProvider instance:
    - 'gemini' (default): calls Google Gemini API.
    - 'mock': deterministic fallback for testing or when Google API has demand spikes.
    """
    provider_name = settings.llm_provider.lower()

    if provider_name == "gemini":
        return GeminiProvider()
    if provider_name == "mock":
        return MockLLMProvider()

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider_name}")


__all__ = [
    "LLMError",
    "LLMProvider",
    "LLMUsage",
    "LLMValidationError",
    "get_llm",
]
