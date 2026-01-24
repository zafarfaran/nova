"""VAT Period model for tracking VAT return periods."""

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.evidence import EvidenceItem


class PeriodStatus(str, enum.Enum):
    """Status of a VAT period."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    READY = "ready"
    SUBMITTED = "submitted"
    LOCKED = "locked"


class VATPeriod(Base, TimestampMixin):
    """VAT return period for a client."""

    __tablename__ = "vat_periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[PeriodStatus] = mapped_column(
        Enum(PeriodStatus), default=PeriodStatus.DRAFT
    )
    is_locked: Mapped[bool] = mapped_column(default=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(String(2000))

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="vat_periods")
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        "EvidenceItem", back_populates="vat_period", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VATPeriod(id={self.id}, client_id={self.client_id}, {self.period_start} - {self.period_end})>"
