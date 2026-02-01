"""Backward compatibility: Re-export from new location."""

from app.models.documents import Document, DocumentStatus

__all__ = ["Document", "DocumentStatus"]
