"""Backward compatibility: Re-export from new location."""

from app.models.documents import DocumentVersion, ExtractionStatus

__all__ = ["DocumentVersion", "ExtractionStatus"]
