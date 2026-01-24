"""ChecklistItem model for document tracking."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client


class ChecklistItem(Base, TimestampMixin):
    """Checklist item for document tracking - linked to clients table."""

    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # missing, uploaded, unknown
    acceptance: Mapped[str] = mapped_column(String(50), nullable=False)
    cta_action: Mapped[str] = mapped_column(String(50), nullable=False)
    cta_data: Mapped[str | None] = mapped_column(String(2000))
    uploaded_file_url: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="checklist_items")

    def __repr__(self) -> str:
        return f"<ChecklistItem(id={self.id}, title='{self.title}', status='{self.status}')>"
