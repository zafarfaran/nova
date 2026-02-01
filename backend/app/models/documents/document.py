"""Document model for uploaded files and extracted data."""

import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.validation.validation import ValidationResult
    from app.models.clients.client import Client
    from app.models.engagements.engagement import Engagement
    from app.models.documents.type import DocumentType
    from app.models.clients.counterparty import Counterparty
    from app.models.clients.financial_account import FinancialAccount
    from app.models.documents.version import DocumentVersion
    from app.models.requests.item import RequestItem


class DocumentStatus(str, enum.Enum):
    """Status of document processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    VALIDATED = "validated"
    FAILED = "failed"


class Document(Base, TimestampMixin):
    """Document entity for uploaded files."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign keys
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"), nullable=False, index=True
    )
    engagement_id: Mapped[int | None] = mapped_column(
        ForeignKey("engagements.id"), index=True
    )
    document_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_types.id"), index=True
    )
    counterparty_id: Mapped[int | None] = mapped_column(
        ForeignKey("counterparties.id"), index=True
    )
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("financial_accounts.id"), index=True
    )

    # File information
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column()

    # Document metadata
    title: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(50), default="upload")
    document_date: Mapped[date | None] = mapped_column(Date)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Processing status
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING
    )
    processing_error: Mapped[str | None] = mapped_column(String(2000))

    # Key extracted fields for quick access (denormalized from DocumentVersion)
    invoice_number: Mapped[str | None] = mapped_column(String(100))
    invoice_date: Mapped[date | None] = mapped_column(Date)
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    supplier_vat_number: Mapped[str | None] = mapped_column(String(20))
    customer_name: Mapped[str | None] = mapped_column(String(255))
    customer_vat_number: Mapped[str | None] = mapped_column(String(20))
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    vat_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    gross_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    vat_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    currency: Mapped[str | None] = mapped_column(String(3), default="GBP")
    description: Mapped[str | None] = mapped_column(String(2000))

    # Relationships
    client: Mapped["Client"] = relationship(
        "Client", back_populates="documents"
    )
    engagement: Mapped["Engagement | None"] = relationship(
        "Engagement", back_populates="documents"
    )
    document_type: Mapped["DocumentType | None"] = relationship(
        "DocumentType", back_populates="documents"
    )
    counterparty: Mapped["Counterparty | None"] = relationship(
        "Counterparty", back_populates="documents"
    )
    account: Mapped["FinancialAccount | None"] = relationship(
        "FinancialAccount", back_populates="documents"
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        "ValidationResult", back_populates="document", cascade="all, delete-orphan"
    )
    request_items: Mapped[list["RequestItem"]] = relationship(
        "RequestItem",
        secondary="request_item_documents",
        back_populates="documents"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status={self.status})>"

    def get_latest_version(self) -> "DocumentVersion | None":
        """Get the latest version of this document."""
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.version_no)

    def get_extracted_data(self) -> dict[str, Any] | None:
        """Get extracted data from the latest version."""
        latest = self.get_latest_version()
        if latest and latest.extracted_data:
            return latest.extracted_data
        return None
