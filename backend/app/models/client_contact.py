"""ClientContact model for multiple contacts per client."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client


class ClientContact(Base, TimestampMixin):
    """Contact information for a client - supports multiple contacts per client."""

    __tablename__ = "client_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    
    # Contact details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(100))  # e.g., "owner", "accountant", "admin"
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="contacts")

    def __repr__(self) -> str:
        return f"<ClientContact(id={self.id}, name='{self.name}', email='{self.email}')>"
