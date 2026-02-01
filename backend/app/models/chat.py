"""Backward compatibility: Re-export from new location."""

from app.models.chat import ChatSession, ChatMessage, MessageRole

__all__ = ["ChatSession", "ChatMessage", "MessageRole"]
