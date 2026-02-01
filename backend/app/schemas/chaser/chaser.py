"""Pydantic schemas for Chaser."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.chaser import ChaserStatus


class ChaserRequestCreate(BaseModel):
    """Schema for creating a Chaser Request."""

    engagement_id: int
    recipient_email: EmailStr
    recipient_name: str | None = None
    requested_items: list[str] = []
    due_date: date | None = None


class ChaserRequestResponse(BaseModel):
    """Schema for Chaser Request response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    engagement_id: int
    recipient_email: str
    recipient_name: str | None
    requested_items: list
    upload_token: str
    due_date: date | None
    status: ChaserStatus
    subject: str | None
    message_body: str | None
    sent_at: datetime | None
    last_reminded_at: datetime | None
    reminder_count: int
    created_at: datetime
    updated_at: datetime


class ChaserRequestList(BaseModel):
    """Schema for listing chaser requests."""

    items: list[ChaserRequestResponse]
    total: int


class AutoChaseRequest(BaseModel):
    """Schema for auto-chase request."""

    recipient_email: EmailStr


class ChaserResponseCreate(BaseModel):
    """Schema for creating a Chaser Response."""

    documents_uploaded: int
    responder_email: EmailStr | None = None
    responder_name: str | None = None
    notes: str | None = None


class ChaserResponseResponse(BaseModel):
    """Schema for Chaser Response response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chaser_request_id: int
    responder_email: str | None
    responder_name: str | None
    documents_uploaded: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
