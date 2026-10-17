"""
llm/__init__.py — LLM package initialization.

Provides a factory function `get_llm()` that returns the
configured LLMProvider based on the `.env` setting.
"""

from llm.base import LLMError, LLMProvider, LLMUsage, LLMValidationError
from llm.gemini_provider import GeminiProvider
from config import settings


def get_llm() -> LLMProvider:
    """
    Returns the configured LLMProvider instance.
    Currently only supports 'gemini'.
    """
    provider_name = settings.llm_provider.lower()
    
    if provider_name == "gemini":
        return GeminiProvider()
    
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider_name}")


__all__ = [
    "LLMError",
    "LLMProvider",
    "LLMUsage",
    "LLMValidationError",
    "get_llm",
]
