"""AutoChaser model for automated reminder emails."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client


class AutoChaser(Base, TimestampMixin):
    """Auto chaser for automated reminder emails - linked to clients table."""

    __tablename__ = "auto_chasers"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    delay_days: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="auto_chasers")

    def __repr__(self) -> str:
        return f"<AutoChaser(id={self.id}, trigger='{self.trigger}')>"
