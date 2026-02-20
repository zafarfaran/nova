"""MeetingNote model — client meeting records.

Adapted from Helio's MeetingNote (helio/apps/api/app/db/models.py).
Changes from Helio original:
  - client_id is Integer FK to Nova's clients.id (was String in Helio)
  - author_id is nullable String with NO FK constraint (Nova has no users table)
  - Uses Nova's Base + TimestampMixin instead of manual timestamps
  - Table renamed to 'tax_meeting_notes' to avoid potential conflicts
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.shared.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid4())


class TaxMeetingNote(Base, TimestampMixin):
    """Record of a client meeting."""

    __tablename__ = "tax_meeting_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    author_id: Mapped[str | None] = mapped_column(String, nullable=True)  # No FK — Nova has no users table
    meeting_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    attendees: Mapped[str | None] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[list | None] = mapped_column(JSON, default=list)
    tags: Mapped[list | None] = mapped_column(JSON, default=list)

    def __repr__(self) -> str:
        return f"<TaxMeetingNote(id={self.id}, client_id={self.client_id}, subject='{self.subject}')>"
