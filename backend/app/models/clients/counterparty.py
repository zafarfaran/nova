"""Counterparty model for tracking suppliers and customers."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.clients.client import Client
    from app.models.documents.document import Document


class CounterpartyType(str, enum.Enum):
    """Type of counterparty."""
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    BOTH = "both"


class Counterparty(Base, TimestampMixin):
    """Counterparty entity for tracking suppliers and customers.
    
    This allows documents to be linked to specific suppliers/customers
    for better organization and validation.
    """

    __tablename__ = "counterparties"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    
    # Counterparty details
    counterparty_type: Mapped[CounterpartyType] = mapped_column(
        Enum(CounterpartyType), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    vat_number: Mapped[str | None] = mapped_column(String(20))
    external_ref: Mapped[str | None] = mapped_column(String(100))  # External system reference
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="counterparties")
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="counterparty", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Counterparty(id={self.id}, name='{self.name}', type={self.counterparty_type})>"
