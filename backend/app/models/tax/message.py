"""Message model — tax chat messages.

Adapted from Helio's Message (helio/apps/api/app/db/models.py).
Changes from Helio original:
  - FK to tax_conversations.id (was conversations.id in Helio)
  - Uses Nova's Base + TimestampMixin instead of manual created_at
  - Table renamed to 'tax_messages' to avoid conflict with Nova's chat_messages
"""

from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid4())


class TaxMessage(Base, TimestampMixin):
    """A message in a tax conversation."""

    __tablename__ = "tax_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("tax_conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    insights: Mapped[list | None] = mapped_column(JSON, default=list)
    tool_calls: Mapped[list | None] = mapped_column(JSON, default=list)
    dashboard_data: Mapped[dict | None] = mapped_column(JSON)
    model: Mapped[str | None] = mapped_column(String)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    conversation: Mapped["TaxConversation"] = relationship(
        "TaxConversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<TaxMessage(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"
