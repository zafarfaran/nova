"""RequestSet model - groups document requests for an engagement."""

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.engagement import Engagement
    from app.models.request_item import RequestItem


class RequestSetStatus(str, enum.Enum):
    """Status of a request set."""
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    COMPLETE = "complete"
    EXPIRED = "expired"


class RequestSet(Base, TimestampMixin):
    """Request set entity - groups document requests for an engagement.
    
    This replaces the EvidenceItem concept with a more flexible request system
    that can track multiple document requests as a batch.
    """

    __tablename__ = "request_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"), nullable=False, index=True)
    
    # Request details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[RequestSetStatus] = mapped_column(
        Enum(RequestSetStatus), default=RequestSetStatus.DRAFT
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    
    # Communication
    upload_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    sent_at: Mapped[date | None] = mapped_column(Date)
    
    # Relationships
    engagement: Mapped["Engagement"] = relationship("Engagement", back_populates="request_sets")
    items: Mapped[list["RequestItem"]] = relationship(
        "RequestItem", back_populates="request_set", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RequestSet(id={self.id}, name='{self.name}', status={self.status})>"
