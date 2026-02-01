"""Backward compatibility: Re-export from new location."""

from app.services.chat import ChatService

__all__ = ["ChatService"]
