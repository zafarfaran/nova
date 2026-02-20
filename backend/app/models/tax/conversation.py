"""Conversation model — tax chat sessions.

Adapted from Helio's Conversation (helio/apps/api/app/db/models.py).
Changes from Helio original:
  - client_id is Integer FK to Nova's clients.id (was String in Helio)
  - user_id is nullable String with NO FK constraint (Nova has no users table)
  - Uses Nova's Base + TimestampMixin instead of manual timestamps
  - Table renamed to 'tax_conversations' to avoid conflict with Nova's chat_sessions
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid4())


class TaxConversation(Base, TimestampMixin):
    """A tax-focused chat session with a client."""

    __tablename__ = "tax_conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)  # No FK — Nova has no users table
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")
    last_message_preview: Mapped[str | None] = mapped_column(String)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    unread: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[list | None] = mapped_column(JSON, default=list)
    tax_plan_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    messages: Mapped[list["TaxMessage"]] = relationship(
        "TaxMessage",
        back_populates="conversation",
        order_by="TaxMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<TaxConversation(id={self.id}, client_id={self.client_id}, title='{self.title}')>"
