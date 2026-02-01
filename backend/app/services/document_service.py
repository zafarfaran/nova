"""Backward compatibility: Re-export from new location."""

from app.services.documents import DocumentService

__all__ = ["DocumentService"]
