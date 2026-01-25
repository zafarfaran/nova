"""Document model for uploaded files and extracted data."""

import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.evidence import EvidenceItem
    from app.models.validation import ValidationResult


class DocumentStatus(str, enum.Enum):
    """Status of document processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    VALIDATED = "validated"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    """Type of document."""

    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    RECEIPT = "receipt"
    BANK_STATEMENT = "bank_statement"
    PAYROLL = "payroll"
    CONTRACT = "contract"
    IMPORT_DECLARATION = "import_declaration"
    EXPORT_DECLARATION = "export_declaration"
    VAT_CERTIFICATE = "vat_certificate"
    OTHER = "other"


class Document(Base, TimestampMixin):
    """Document entity for uploaded files."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("evidence_items.id")
    )

    # File information
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column()

    # Processing status
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING
    )
    document_type: Mapped[DocumentType | None] = mapped_column(Enum(DocumentType))
    processing_error: Mapped[str | None] = mapped_column(String(2000))

    # Extracted fields (from AI processing)
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Key extracted fields for quick access
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
    evidence_item: Mapped["EvidenceItem | None"] = relationship(
        "EvidenceItem", back_populates="documents"
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        "ValidationResult", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status={self.status})>"
