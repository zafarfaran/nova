"""Chaser model for tracking evidence requests and reminders."""

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.vat_period import VATPeriod


class ChaserStatus(str, enum.Enum):
    """Status of a chaser request."""

    DRAFT = "draft"
    SENT = "sent"
    REMINDED = "reminded"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETE = "complete"
    EXPIRED = "expired"


class ChaserRequest(Base, TimestampMixin):
    """Request for missing VAT evidence."""

    __tablename__ = "chaser_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    vat_period_id: Mapped[int] = mapped_column(
        ForeignKey("vat_periods.id"), nullable=False
    )

    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_name: Mapped[str | None] = mapped_column(String(255))

    # Requested items (JSON list of item descriptions)
    requested_items: Mapped[list] = mapped_column(JSON, default=list)

    # Upload token for secure uploads
    upload_token: Mapped[str] = mapped_column(
        String(64), unique=True, default=lambda: uuid.uuid4().hex
    )

    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[ChaserStatus] = mapped_column(
        Enum(ChaserStatus), default=ChaserStatus.DRAFT
    )

    # Email content
    subject: Mapped[str | None] = mapped_column(String(255))
    message_body: Mapped[str | None] = mapped_column(String(5000))

    # Tracking
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_count: Mapped[int] = mapped_column(default=0)

    # Relationships
    vat_period: Mapped["VATPeriod"] = relationship("VATPeriod")

    def __repr__(self) -> str:
        return f"<ChaserRequest(id={self.id}, recipient={self.recipient_email}, status={self.status})>"


class ChaserResponse(Base, TimestampMixin):
    """Response to a chaser request (document upload via token)."""

    __tablename__ = "chaser_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    chaser_request_id: Mapped[int] = mapped_column(
        ForeignKey("chaser_requests.id"), nullable=False
    )

    # Response tracking
    responder_email: Mapped[str | None] = mapped_column(String(255))
    responder_name: Mapped[str | None] = mapped_column(String(255))
    documents_uploaded: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(String(2000))

    # Relationship
    chaser_request: Mapped["ChaserRequest"] = relationship("ChaserRequest")

    def __repr__(self) -> str:
        return f"<ChaserResponse(id={self.id}, chaser_request_id={self.chaser_request_id})>"
