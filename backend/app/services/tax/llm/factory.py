"""LLM provider factory."""

import logging

from app.config import get_settings
from app.services.tax.llm.claude import ClaudeProvider

logger = logging.getLogger(__name__)

_provider = None


def get_llm_provider() -> ClaudeProvider:
    global _provider
    if _provider is None:
        settings = get_settings()
        if settings.anthropic_api_key:
            _provider = ClaudeProvider()
            logger.info("LLM provider: Claude, model=%s", settings.ai_model)
        else:
            raise RuntimeError(
                "No LLM provider configured — set ANTHROPIC_API_KEY"
            )
    return _provider
