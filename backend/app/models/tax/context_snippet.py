"""ContextSnippet model — web content captures.

Adapted from Helio's ContextSnippet (helio/apps/api/app/db/models.py).
Changes from Helio original:
  - user_id is nullable String with NO FK constraint (Nova has no users table)
  - Uses Nova's Base + TimestampMixin instead of manual created_at
  - Table renamed to 'tax_context_snippets' to avoid potential conflicts
"""

from uuid import uuid4

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.shared.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid4())


class TaxContextSnippet(Base, TimestampMixin):
    """Web page content captured by the browser extension."""

    __tablename__ = "tax_context_snippets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)  # No FK — Nova has no users table
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    source_title: Mapped[str] = mapped_column(String, nullable=False, default="")
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    capture_type: Mapped[str] = mapped_column(String, nullable=False, default="full_page")
    status: Mapped[str] = mapped_column(String, nullable=False, default="processing")
    is_consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<TaxContextSnippet(id={self.id}, source_url='{self.source_url}')>"
