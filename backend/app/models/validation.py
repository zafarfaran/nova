"""Validation model for document validation results."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document import Document


class RuleType(str, enum.Enum):
    """Type of validation rule."""

    REQUIRED_FIELDS = "required_fields"
    VAT_NUMBER_FORMAT = "vat_number_format"
    DATE_IN_PERIOD = "date_in_period"
    TOTALS_MATCH = "totals_match"
    VAT_RATE_VALID = "vat_rate_valid"
    DUPLICATE_DETECTION = "duplicate_detection"
    AI_ANOMALY = "ai_anomaly"
    CURRENCY_VALID = "currency_valid"
    SUPPLIER_VALID = "supplier_valid"


class ValidationStatus(str, enum.Enum):
    """Status of validation result."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class ValidationResult(Base, TimestampMixin):
    """Validation result for a document."""

    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"), nullable=False
    )
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType), nullable=False)
    status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus), nullable=False
    )
    message: Mapped[str | None] = mapped_column(String(1000))
    details: Mapped[str | None] = mapped_column(String(2000))
    field_name: Mapped[str | None] = mapped_column(String(100))
    expected_value: Mapped[str | None] = mapped_column(String(500))
    actual_value: Mapped[str | None] = mapped_column(String(500))

    # AI anomaly detection fields
    severity: Mapped[str | None] = mapped_column(String(20))  # high, medium, low
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))  # 0.00 - 1.00
    ai_reasoning: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Review fields for human review workflow
    reviewed_at: Mapped[datetime | None] = mapped_column()
    reviewed_by: Mapped[str | None] = mapped_column(String(255))
    review_action: Mapped[str | None] = mapped_column(String(50))  # approved, rejected, request_info

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="validation_results"
    )

    def __repr__(self) -> str:
        return f"<ValidationResult(id={self.id}, rule={self.rule_type}, status={self.status})>"
