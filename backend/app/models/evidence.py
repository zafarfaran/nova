"""Evidence models for tracking VAT evidence items and coverage."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.vat_period import VATPeriod


class EvidenceCategory(str, enum.Enum):
    """Categories of VAT evidence."""

    SALES_INVOICES = "sales_invoices"
    PURCHASE_INVOICES = "purchase_invoices"
    CREDIT_NOTES = "credit_notes"
    DEBIT_NOTES = "debit_notes"
    BANK_STATEMENTS = "bank_statements"
    RECEIPTS = "receipts"
    CONTRACTS = "contracts"
    IMPORT_DOCUMENTS = "import_documents"
    EXPORT_DOCUMENTS = "export_documents"
    VAT_CERTIFICATES = "vat_certificates"
    OTHER = "other"


class EvidenceStatus(str, enum.Enum):
    """Status of an evidence item."""

    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETE = "complete"
    VALIDATED = "validated"
    EXCEPTION = "exception"


class EvidenceItem(Base, TimestampMixin):
    """An evidence item required for VAT compliance."""

    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    vat_period_id: Mapped[int] = mapped_column(
        ForeignKey("vat_periods.id"), nullable=False
    )
    category: Mapped[EvidenceCategory] = mapped_column(
        Enum(EvidenceCategory), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus), default=EvidenceStatus.PENDING
    )
    expected_count: Mapped[int] = mapped_column(Integer, default=0)
    received_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(String(2000))

    # Relationships
    vat_period: Mapped["VATPeriod"] = relationship(
        "VATPeriod", back_populates="evidence_items"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="evidence_item"
    )

    def __repr__(self) -> str:
        return f"<EvidenceItem(id={self.id}, category={self.category}, status={self.status})>"

    @property
    def coverage_percentage(self) -> float:
        """Calculate coverage percentage."""
        if self.expected_count == 0:
            return 100.0 if self.received_count > 0 else 0.0
        return min((self.received_count / self.expected_count) * 100, 100.0)

    @property
    def is_complete(self) -> bool:
        """Check if evidence is complete."""
        return self.received_count >= self.expected_count and self.expected_count > 0
