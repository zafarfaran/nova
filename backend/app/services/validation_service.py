"""Service layer for document validation."""

import re
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.vat_rules import (
    CALCULATION_TOLERANCE,
    VALID_VAT_RATES,
    VAT_NUMBER_PATTERN,
)
from app.models.document import Document, DocumentStatus
from app.models.evidence import EvidenceItem
from app.models.validation import RuleType, ValidationResult, ValidationStatus
from app.models.vat_period import VATPeriod


class ValidationService:
    """Service for validating documents."""

    def __init__(self, db: Session):
        self.db = db

    def validate_document(self, document_id: int) -> list[ValidationResult]:
        """Run all validation rules on a document.

        Returns list of validation results.
        """
        doc = self.db.get(Document, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Clear existing validation results
        self._clear_results(document_id)

        results = []

        # Run all validation rules
        results.append(self._validate_required_fields(doc))
        results.append(self._validate_vat_number_format(doc))
        results.append(self._validate_date_in_period(doc))
        results.append(self._validate_totals_match(doc))
        results.append(self._validate_vat_rate(doc))
        results.append(self._validate_duplicate(doc))
        results.append(self._validate_currency(doc))

        # Save all results
        for result in results:
            self.db.add(result)

        # Update document status based on results
        has_failures = any(r.status == ValidationStatus.FAILED for r in results)
        if has_failures:
            doc.status = DocumentStatus.EXTRACTED  # Keep as extracted, not validated
        else:
            doc.status = DocumentStatus.VALIDATED

        self.db.commit()

        for result in results:
            self.db.refresh(result)

        return results

    def _clear_results(self, document_id: int) -> None:
        """Clear existing validation results for a document."""
        stmt = select(ValidationResult).where(
            ValidationResult.document_id == document_id
        )
        existing = list(self.db.scalars(stmt).all())
        for result in existing:
            self.db.delete(result)

    def _validate_required_fields(self, doc: Document) -> ValidationResult:
        """Validate that required fields are present."""
        required_fields = [
            ("invoice_number", doc.invoice_number),
            ("invoice_date", doc.invoice_date),
            ("supplier_name", doc.supplier_name),
            ("net_amount", doc.net_amount),
            ("vat_amount", doc.vat_amount),
            ("gross_amount", doc.gross_amount),
        ]

        missing = [name for name, value in required_fields if value is None]

        if missing:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.REQUIRED_FIELDS,
                status=ValidationStatus.FAILED,
                message=f"Missing required fields: {', '.join(missing)}",
                details=f"The following fields are required but not extracted: {missing}",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.REQUIRED_FIELDS,
            status=ValidationStatus.PASSED,
            message="All required fields present",
        )

    def _validate_vat_number_format(self, doc: Document) -> ValidationResult:
        """Validate UK VAT number format."""
        vat_numbers = []
        if doc.supplier_vat_number:
            vat_numbers.append(("supplier", doc.supplier_vat_number))
        if doc.customer_vat_number:
            vat_numbers.append(("customer", doc.customer_vat_number))

        if not vat_numbers:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_NUMBER_FORMAT,
                status=ValidationStatus.WARNING,
                message="No VAT numbers to validate",
            )

        invalid = []
        for party, vat_number in vat_numbers:
            if not re.match(VAT_NUMBER_PATTERN, vat_number):
                invalid.append(f"{party}: {vat_number}")

        if invalid:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_NUMBER_FORMAT,
                status=ValidationStatus.FAILED,
                message=f"Invalid VAT number format: {', '.join(invalid)}",
                details="UK VAT numbers should be in format GB followed by 9 or 12 digits",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_NUMBER_FORMAT,
            status=ValidationStatus.PASSED,
            message="VAT number format valid",
        )

    def _validate_date_in_period(self, doc: Document) -> ValidationResult:
        """Validate that invoice date falls within the VAT period."""
        if not doc.invoice_date:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.SKIPPED,
                message="No invoice date to validate",
            )

        if not doc.evidence_item_id:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.SKIPPED,
                message="Document not linked to evidence item",
            )

        evidence_item = self.db.get(EvidenceItem, doc.evidence_item_id)
        if not evidence_item:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.SKIPPED,
                message="Evidence item not found",
            )

        period = self.db.get(VATPeriod, evidence_item.vat_period_id)
        if not period:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.SKIPPED,
                message="VAT period not found",
            )

        if period.period_start <= doc.invoice_date <= period.period_end:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.PASSED,
                message="Invoice date within VAT period",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DATE_IN_PERIOD,
            status=ValidationStatus.FAILED,
            message=f"Invoice date {doc.invoice_date} outside VAT period "
            f"({period.period_start} - {period.period_end})",
            field_name="invoice_date",
            expected_value=f"{period.period_start} - {period.period_end}",
            actual_value=str(doc.invoice_date),
        )

    def _validate_totals_match(self, doc: Document) -> ValidationResult:
        """Validate that net + VAT = gross."""
        if doc.net_amount is None or doc.vat_amount is None or doc.gross_amount is None:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.TOTALS_MATCH,
                status=ValidationStatus.SKIPPED,
                message="Missing amount fields for calculation validation",
            )

        calculated_gross = doc.net_amount + doc.vat_amount
        difference = abs(calculated_gross - doc.gross_amount)

        if difference <= CALCULATION_TOLERANCE:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.TOTALS_MATCH,
                status=ValidationStatus.PASSED,
                message="Net + VAT = Gross calculation verified",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.TOTALS_MATCH,
            status=ValidationStatus.FAILED,
            message=f"Total mismatch: {doc.net_amount} + {doc.vat_amount} = "
            f"{calculated_gross}, but gross is {doc.gross_amount}",
            field_name="gross_amount",
            expected_value=str(calculated_gross),
            actual_value=str(doc.gross_amount),
        )

    def _validate_vat_rate(self, doc: Document) -> ValidationResult:
        """Validate that VAT rate is a valid UK rate."""
        if doc.vat_rate is None:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,
                status=ValidationStatus.SKIPPED,
                message="No VAT rate to validate",
            )

        if doc.vat_rate in VALID_VAT_RATES:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,
                status=ValidationStatus.PASSED,
                message=f"VAT rate {doc.vat_rate}% is valid",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_RATE_VALID,
            status=ValidationStatus.WARNING,
            message=f"Non-standard VAT rate: {doc.vat_rate}%",
            details=f"Standard UK VAT rates are: {[str(r) for r in VALID_VAT_RATES]}",
            field_name="vat_rate",
            expected_value=str(list(VALID_VAT_RATES)),
            actual_value=str(doc.vat_rate),
        )

    def _validate_duplicate(self, doc: Document) -> ValidationResult:
        """Check for potential duplicate documents."""
        if not doc.invoice_number:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DUPLICATE_DETECTION,
                status=ValidationStatus.SKIPPED,
                message="No invoice number for duplicate check",
            )

        # Find documents with same invoice number
        stmt = select(Document).where(
            Document.invoice_number == doc.invoice_number,
            Document.id != doc.id,
        )
        duplicates = list(self.db.scalars(stmt).all())

        if duplicates:
            dup_ids = [str(d.id) for d in duplicates]
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DUPLICATE_DETECTION,
                status=ValidationStatus.WARNING,
                message=f"Potential duplicates found: document IDs {', '.join(dup_ids)}",
                details=f"Documents with same invoice number: {doc.invoice_number}",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DUPLICATE_DETECTION,
            status=ValidationStatus.PASSED,
            message="No duplicates found",
        )

    def _validate_currency(self, doc: Document) -> ValidationResult:
        """Validate currency is supported."""
        if not doc.currency:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.CURRENCY_VALID,
                status=ValidationStatus.SKIPPED,
                message="No currency to validate",
            )

        # For UK VAT, GBP is expected, but EUR and USD are common
        supported_currencies = {"GBP", "EUR", "USD"}

        if doc.currency in supported_currencies:
            if doc.currency != "GBP":
                return ValidationResult(
                    document_id=doc.id,
                    rule_type=RuleType.CURRENCY_VALID,
                    status=ValidationStatus.WARNING,
                    message=f"Non-GBP currency: {doc.currency}",
                    details="May need exchange rate conversion for UK VAT return",
                )
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.CURRENCY_VALID,
                status=ValidationStatus.PASSED,
                message="Currency valid (GBP)",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.CURRENCY_VALID,
            status=ValidationStatus.WARNING,
            message=f"Unusual currency: {doc.currency}",
            details="Verify currency is correct and apply appropriate exchange rate",
        )

    def get_validation_results(self, document_id: int) -> list[ValidationResult]:
        """Get all validation results for a document."""
        stmt = select(ValidationResult).where(
            ValidationResult.document_id == document_id
        )
        return list(self.db.scalars(stmt).all())

    def get_validation_summary(self, period_id: int) -> dict:
        """Get validation summary for a VAT period."""
        # Get all documents for the period
        stmt = (
            select(Document)
            .join(EvidenceItem)
            .where(EvidenceItem.vat_period_id == period_id)
        )
        documents = list(self.db.scalars(stmt).all())

        total_docs = len(documents)
        validated_docs = sum(1 for d in documents if d.status == DocumentStatus.VALIDATED)
        failed_docs = sum(1 for d in documents if d.status == DocumentStatus.FAILED)
        pending_docs = sum(
            1
            for d in documents
            if d.status in [DocumentStatus.PENDING, DocumentStatus.PROCESSING]
        )

        # Get all validation results for the period
        all_results = []
        for doc in documents:
            results = self.get_validation_results(doc.id)
            all_results.extend(results)

        passed = sum(1 for r in all_results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in all_results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in all_results if r.status == ValidationStatus.WARNING)

        return {
            "vat_period_id": period_id,
            "total_documents": total_docs,
            "validated_documents": validated_docs,
            "failed_documents": failed_docs,
            "pending_documents": pending_docs,
            "total_validations": len(all_results),
            "passed_validations": passed,
            "failed_validations": failed,
            "warning_validations": warnings,
            "validation_rate": (validated_docs / total_docs * 100) if total_docs > 0 else 0,
        }
