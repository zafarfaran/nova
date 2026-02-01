"""Backward compatibility: Re-export from new location."""

from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
)

__all__ = [
    "ChatSessionCreate",
    "ChatSessionResponse",
    "ChatMessageResponse",
    "ChatRequest",
    "ChatResponse",
]
