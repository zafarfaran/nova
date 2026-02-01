"""Pydantic schemas for Document."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentBase(BaseModel):
    """Base schema for Document."""

    engagement_id: int | None = None
    document_type_id: int | None = None


class DocumentCreate(DocumentBase):
    """Schema for creating a Document (internal use)."""

    client_id: int
    filename: str
    s3_key: str
    file_hash: str
    content_type: str | None = None
    file_size: int | None = None


class DocumentUpdate(BaseModel):
    """Schema for updating a Document."""

    engagement_id: int | None = None
    document_type_id: int | None = None
    status: DocumentStatus | None = None


class ExtractedData(BaseModel):
    """Schema for extracted document data."""

    invoice_number: str | None = None
    invoice_date: date | None = None
    supplier_name: str | None = None
    supplier_vat_number: str | None = None
    customer_name: str | None = None
    customer_vat_number: str | None = None
    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    gross_amount: Decimal | None = None
    vat_rate: Decimal | None = None
    currency: str | None = None
    description: str | None = None
    raw_data: dict[str, Any] | None = None


class DocumentResponse(BaseModel):
    """Schema for Document response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    engagement_id: int | None
    document_type_id: int | None
    filename: str
    s3_key: str
    file_hash: str
    content_type: str | None
    file_size: int | None
    status: DocumentStatus
    processing_error: str | None
    invoice_number: str | None
    invoice_date: date | None
    supplier_name: str | None
    supplier_vat_number: str | None
    customer_name: str | None
    customer_vat_number: str | None
    net_amount: Decimal | None
    vat_amount: Decimal | None
    gross_amount: Decimal | None
    vat_rate: Decimal | None
    currency: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    """Schema for listing documents."""

    items: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    document_id: int
    filename: str
    status: DocumentStatus
    is_duplicate: bool = False
    duplicate_document_id: int | None = None


class PresignedUrlResponse(BaseModel):
    """Schema for presigned URL response."""

    url: str
    expires_in: int
