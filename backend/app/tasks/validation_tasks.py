"""Backward compatibility: Re-export from new location."""

from app.tasks.validation import (
    validate_document,
    validate_engagement_documents,
    validate_client_documents,
    validate_period_documents,
)

__all__ = [
    "validate_document",
    "validate_engagement_documents",
    "validate_client_documents",
    "validate_period_documents",
]
