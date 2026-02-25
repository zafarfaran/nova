"""Backward compatibility: Re-export from new location."""

from app.services.documents import PDFExtractionService

__all__ = ["PDFExtractionService"]
