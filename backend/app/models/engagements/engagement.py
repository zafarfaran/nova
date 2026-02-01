"""Engagement model - replaces VATPeriod with a more generic engagement concept."""

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.clients.client import Client
    from app.models.documents.document import Document
    from app.models.requests.set import RequestSet
    from app.models.audit.log import AuditLog
    from app.models.chaser.chaser import ChaserRequest


class EngagementType(str, enum.Enum):
    """Type of engagement."""
    VAT_RETURN = "vat_return"
    ANNUAL_ACCOUNTS = "annual_accounts"
    TAX_RETURN = "tax_return"
    AUDIT = "audit"
    BOOKKEEPING = "bookkeeping"
    OTHER = "other"


class EngagementStatus(str, enum.Enum):
    """Status of an engagement."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    READY = "ready"
    SUBMITTED = "submitted"
    LOCKED = "locked"


class Engagement(Base, TimestampMixin):
    """Engagement entity - represents a specific work engagement for a client.
    
    This replaces VATPeriod with a more flexible engagement model that can
    represent VAT returns, annual accounts, tax returns, or any other engagement.
    """

    __tablename__ = "engagements"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    
    # Engagement details
    engagement_type: Mapped[EngagementType] = mapped_column(
        Enum(EngagementType), default=EngagementType.VAT_RETURN
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[EngagementStatus] = mapped_column(
        Enum(EngagementStatus), default=EngagementStatus.DRAFT
    )
    
    # Optional metadata
    reference: Mapped[str | None] = mapped_column(String(100))
    due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(String(2000))
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="engagements")
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="engagement", cascade="all, delete-orphan"
    )
    request_sets: Mapped[list["RequestSet"]] = relationship(
        "RequestSet", back_populates="engagement", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="engagement", cascade="all, delete-orphan"
    )
    chaser_requests: Mapped[list["ChaserRequest"]] = relationship(
        "ChaserRequest", back_populates="engagement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Engagement(id={self.id}, type={self.engagement_type}, period={self.period_start}-{self.period_end})>"
