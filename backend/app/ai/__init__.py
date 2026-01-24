"""AI provider factory and utilities."""

from functools import lru_cache

from app.ai.anthropic_provider import AnthropicProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.provider import AIProvider
from app.config import get_settings


@lru_cache
def get_ai_provider() -> AIProvider:
    """Get the configured AI provider instance.

    Returns the appropriate provider based on the AI_PROVIDER setting.
    Cached for reuse across requests.
    """
    settings = get_settings()

    if settings.ai_provider == "openai":
        return OpenAIProvider()
    elif settings.ai_provider == "anthropic":
        return AnthropicProvider()
    else:
        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")


__all__ = [
    "AIProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "get_ai_provider",
]
