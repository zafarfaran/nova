"""Document domain schemas."""

from app.schemas.documents.document import (
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
