"""AI provider factory and utilities."""

from functools import lru_cache

from app.ai.anthropic_chat_provider import AnthropicChatProvider
from app.ai.anthropic_provider import AnthropicProvider
from app.ai.chat_provider import ChatProvider
from app.ai.openai_chat_provider import OpenAIChatProvider
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


@lru_cache
def get_chat_provider() -> ChatProvider:
    """Get the configured chat provider instance.

    Returns the appropriate chat provider based on the AI_PROVIDER setting.
    Cached for reuse across requests.
    """
    settings = get_settings()

    if settings.ai_provider == "openai":
        return OpenAIChatProvider()
    elif settings.ai_provider == "anthropic":
        return AnthropicChatProvider()
    else:
        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")


__all__ = [
    "AIProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "ChatProvider",
    "OpenAIChatProvider",
    "AnthropicChatProvider",
    "get_ai_provider",
    "get_chat_provider",
]
