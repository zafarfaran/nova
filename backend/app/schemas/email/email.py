"""Email schemas for request/response validation."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class EmailPurpose(str, Enum):
    """Email purpose types for AI context."""

    REMINDER = "reminder"
    MISSING_DOCUMENTS = "missing_documents"
    VAT_RETURN_READY = "vat_return_ready"
    VALIDATION_ISSUES = "validation_issues"
    GENERAL = "general"
    WELCOME = "welcome"
    INVOICE_REQUEST = "invoice_request"
    FOLLOW_UP = "follow_up"


class EmailTone(str, Enum):
    """Email tone for AI generation."""

    FORMAL = "formal"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    URGENT = "urgent"


class EmailRequest(BaseModel):
    """Request schema for sending emails."""

    to_email: EmailStr = Field(..., description="Recipient email address")
    to_name: str | None = Field(None, description="Recipient name")
    subject: str | None = Field(None, description="Email subject (will be AI-generated if not provided)")
    body: str | None = Field(None, description="Email body (will be AI-generated if not provided)")

    # AI Generation Parameters
    purpose: EmailPurpose = Field(EmailPurpose.GENERAL, description="Purpose of the email for AI context")
    tone: EmailTone = Field(EmailTone.PROFESSIONAL, description="Tone of the email")
    client_id: int | None = Field(None, description="Client ID for context")
    context_data: dict | None = Field(None, description="Additional context data for AI generation")

    # Optional fields
    cc: list[EmailStr] | None = Field(None, description="CC recipients")
    bcc: list[EmailStr] | None = Field(None, description="BCC recipients")
    reply_to: EmailStr | None = Field(None, description="Reply-to email address")


class AIEmailGenerationRequest(BaseModel):
    """Request for AI to generate email content."""

    purpose: EmailPurpose
    tone: EmailTone
    recipient_name: str | None = None
    client_name: str | None = None
    context_data: dict | None = None


class EmailResponse(BaseModel):
    """Response schema after sending email."""

    success: bool
    message: str
    message_id: str | None = None
    generated_subject: str | None = None
    generated_body: str | None = None
    sent_at: datetime | None = None
