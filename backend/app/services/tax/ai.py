"""AI orchestration service.

Handles interaction with AI providers (Anthropic Claude, OpenAI)
for tax planning conversations and document analysis.
"""

import logging

logger = logging.getLogger(__name__)


def generate_response(messages: list[dict[str, str]]) -> str:
    """Generate an AI response (placeholder).

    Will orchestrate calls to Claude/OpenAI with tax context,
    tool use for calculations, and streaming responses.
    """
    logger.info("AI response requested, message_count=%d", len(messages))
    raise NotImplementedError("AI service not yet implemented")
