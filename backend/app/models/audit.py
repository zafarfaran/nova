"""Audit trail model for tracking all actions."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.vat_period import VATPeriod


class AuditTrailEntry(Base, TimestampMixin):
    """Audit trail entry for tracking all actions on a VAT period."""

    __tablename__ = "audit_trail_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    vat_period_id: Mapped[int] = mapped_column(
        ForeignKey("vat_periods.id"), nullable=False
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    performed_by: Mapped[str | None] = mapped_column(String(255))
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Related entity details
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column()
    old_value: Mapped[str | None] = mapped_column(String(2000))
    new_value: Mapped[str | None] = mapped_column(String(2000))

    # Relationship
    vat_period: Mapped["VATPeriod"] = relationship("VATPeriod")

    def __repr__(self) -> str:
        return f"<AuditTrailEntry(id={self.id}, action='{self.action}')>"
