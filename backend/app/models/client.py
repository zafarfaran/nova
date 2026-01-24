"""Client model for managing VAT clients."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.vat_period import VATPeriod


class EntityType(str, enum.Enum):
    """Type of business entity."""

    SOLE_TRADER = "sole_trader"
    PARTNERSHIP = "partnership"
    LLP = "llp"
    LIMITED_COMPANY = "limited_company"
    PLC = "plc"
    CHARITY = "charity"
    OTHER = "other"


class Client(Base, TimestampMixin):
    """Client entity for VAT management."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vat_number: Mapped[str | None] = mapped_column(String(20), unique=True)
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType), default=EntityType.LIMITED_COMPANY
    )
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_name: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(String(2000))

    # Relationships
    vat_periods: Mapped[list["VATPeriod"]] = relationship(
        "VATPeriod", back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}', vat_number='{self.vat_number}')>"
