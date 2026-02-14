"""Client model for managing VAT clients."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.clients.contact import ClientContact
    from app.models.engagements.engagement import Engagement
    from app.models.clients.counterparty import Counterparty
    from app.models.clients.financial_account import FinancialAccount
    from app.models.documents.document import Document
    from app.models.audit.log import AuditLog


class EntityType(str, enum.Enum):
    """Type of business entity."""

    SOLE_TRADER = "sole_trader"
    PARTNERSHIP = "partnership"
    LLP = "llp"
    LIMITED_COMPANY = "limited_company"
    PLC = "plc"
    CHARITY = "charity"
    OTHER = "other"


class ClientType(str, enum.Enum):
    """Type of client for scoping document requirements."""
    SOLE_TRADER = "sole_trader"
    LIMITED_COMPANY = "limited_company"


class Client(Base, TimestampMixin):
    """Client entity for VAT management."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Client identification
    client_type: Mapped[str | None] = mapped_column(String(50))  # sole_trader, limited_company
    display_name: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Business identifiers
    vat_number: Mapped[str | None] = mapped_column(String(20), unique=True)
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType), default=EntityType.LIMITED_COMPANY
    )
    country_code: Mapped[str] = mapped_column(String(2), default="GB")
    company_number: Mapped[str | None] = mapped_column(String(20))  # Companies House number
    utr: Mapped[str | None] = mapped_column(String(20))  # Unique Taxpayer Reference
    ni_number: Mapped[str | None] = mapped_column(String(20))  # National Insurance number
    vat_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Contact information
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_name: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    
    # Additional info
    notes: Mapped[str | None] = mapped_column(String(2000))
    vat_scheme: Mapped[str | None] = mapped_column(String(50))
    sales_channels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Relationships
    contacts: Mapped[list["ClientContact"]] = relationship(
        "ClientContact", back_populates="client", cascade="all, delete-orphan"
    )
    engagements: Mapped[list["Engagement"]] = relationship(
        "Engagement", back_populates="client", cascade="all, delete-orphan"
    )
    counterparties: Mapped[list["Counterparty"]] = relationship(
        "Counterparty", back_populates="client", cascade="all, delete-orphan"
    )
    financial_accounts: Mapped[list["FinancialAccount"]] = relationship(
        "FinancialAccount", back_populates="client", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="client", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}', vat_number='{self.vat_number}')>"
