"""Backward compatibility: Re-export from new location."""

from app.models.documents import DocumentCategory, DocumentType

__all__ = ["DocumentCategory", "DocumentType"]
