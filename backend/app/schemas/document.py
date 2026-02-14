"""Backward compatibility: Re-export from new location."""

from app.schemas.documents import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    ExtractedData,
    DocumentResponse,
    DocumentList,
    DocumentUploadResponse,
    PresignedUrlResponse,
)

__all__ = [
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "ExtractedData",
    "DocumentResponse",
    "DocumentList",
    "DocumentUploadResponse",
    "PresignedUrlResponse",
]
