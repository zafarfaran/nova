"""Observation model — tax planning insights per client.

Adapted from Helio's Observation (helio/apps/api/app/db/models.py).
Changes from Helio original:
  - client_id is Integer FK to Nova's clients.id (was String in Helio)
  - Uses Nova's Base + TimestampMixin instead of manual timestamps
  - Table renamed to 'tax_observations' to avoid potential conflicts
"""

from uuid import uuid4

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.shared.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid4())


class TaxObservation(Base, TimestampMixin):
    """Tax planning insight or observation for a client."""

    __tablename__ = "tax_observations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    tax_year: Mapped[str | None] = mapped_column(String)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    potential_saving: Mapped[float | None] = mapped_column(Float)
    deadline: Mapped[str | None] = mapped_column(String)
    action_required: Mapped[str | None] = mapped_column(String)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="engine")

    def __repr__(self) -> str:
        return f"<TaxObservation(id={self.id}, client_id={self.client_id}, title='{self.title}')>"
