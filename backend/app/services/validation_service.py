"""Service layer for document validation."""

import asyncio
import logging
import re
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agents import AgentRegistry, Severity as AgentSeverity
from app.ai.anthropic_provider import AnthropicProvider
from app.core.vat_rules import (
    CALCULATION_TOLERANCE,
    VALID_VAT_RATES,
    VAT_NUMBER_PATTERN,
)
from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion
from app.utils.bank_statement_tools import reconcile_balances
from app.models.validation import RuleType, ValidationResult, ValidationStatus
from app.models.engagement import Engagement

logger = logging.getLogger(__name__)


def _send_validation_failure_email_async(db: Session, document_id: int, validation_results: list[ValidationResult]) -> None:
    """Send validation failure email in background (sync wrapper)."""
    import asyncio
    from app.services.email_notification_service import EmailNotificationService

    async def _send():
        email_service = EmailNotificationService(db=db)
        await email_service.send_validation_failure_email(document_id, validation_results)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_send())
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to send validation failure email: {e}", exc_info=True)


class ValidationService:
    """Service for validating documents."""

    # Document type to validator mapping (both lowercase enum values and uppercase for flexibility)
    DOCUMENT_TYPE_VALIDATORS = {
        # Lowercase (Python enum values)
        "invoice": "_validate_invoice",
        "sales_invoice": "_validate_invoice",
        "purchase_invoice": "_validate_invoice",
        "credit_note": "_validate_invoice",
        "bank_statement": "_validate_bank_statement",
        "receipt": "_validate_receipt",
        "expense_receipt": "_validate_receipt",
        "payroll": "_validate_payroll",
        "payslip": "_validate_payroll",
        "payroll_record": "_validate_payroll",
        "vat_certificate": "_validate_vat_certificate",
        "vat_registration": "_validate_vat_certificate",
        "contract": "_validate_contract",
        "agreement": "_validate_contract",
        "service_agreement": "_validate_contract",
        "other": "_validate_generic",
        # Uppercase (for compatibility with frontend/DB values)
        "INVOICE": "_validate_invoice",
        "SALES_INVOICE": "_validate_invoice",
        "PURCHASE_INVOICE": "_validate_invoice",
        "CREDIT_NOTE": "_validate_invoice",
        "BANK_STATEMENT": "_validate_bank_statement",
        "RECEIPT": "_validate_receipt",
        "EXPENSE_RECEIPT": "_validate_receipt",
        "PAYROLL": "_validate_payroll",
        "PAYSLIP": "_validate_payroll",
        "PAYROLL_RECORD": "_validate_payroll",
        "VAT_CERTIFICATE": "_validate_vat_certificate",
        "VAT_REGISTRATION": "_validate_vat_certificate",
        "CONTRACT": "_validate_contract",
        "AGREEMENT": "_validate_contract",
        "SERVICE_AGREEMENT": "_validate_contract",
        "OTHER": "_validate_generic",
    }

    def __init__(self, db: Session, ai_provider: AnthropicProvider | None = None):
        self.db = db
        self._ai_provider = ai_provider

    @property
    def ai_provider(self) -> AnthropicProvider:
        """Lazy-load AI provider."""
        if self._ai_provider is None:
            self._ai_provider = AnthropicProvider()
        return self._ai_provider
    
    def _get_extracted_data(self, doc: Document) -> dict[str, Any] | None:
        """Get extracted data from the document, preferring DocumentVersion if available.
        
        This method provides backwards compatibility - it first checks
        the latest DocumentVersion, then falls back to the document's
        extracted_data field.
        """
        # Try to get from latest DocumentVersion first (new schema)
        if doc.versions:
            latest_version = max(doc.versions, key=lambda v: v.version_no)
            if latest_version.extracted_data:
                logger.debug(
                    "Using extracted_data from DocumentVersion %s for document %s",
                    latest_version.id,
                    doc.id,
                )
                return latest_version.extracted_data
        
        # Fall back to document's extracted_data (legacy)
        return doc.extracted_data

    def validate_document(
        self, document_id: int, include_ai_validation: bool = True
    ) -> list[ValidationResult]:
        """Run document-type-specific validation rules on a document.

        Args:
            document_id: ID of the document to validate
            include_ai_validation: Whether to run AI anomaly detection

        Returns list of validation results.
        """
        doc = self.db.get(Document, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Clear existing validation results
        self._clear_results(document_id)

        results = []

        # Get document type and route to appropriate validator
        if doc.document_type:
            doc_type = doc.document_type.value
        else:
            doc_type = "other"
            logger.warning(f"Document {document_id} has no document_type set, defaulting to 'other'")

        # Look up validator - try both original and uppercase versions
        validator_method_name = self.DOCUMENT_TYPE_VALIDATORS.get(doc_type)
        if not validator_method_name:
            validator_method_name = self.DOCUMENT_TYPE_VALIDATORS.get(doc_type.upper())
        if not validator_method_name:
            # Default to generic validation for unknown types
            validator_method_name = "_validate_generic"
            logger.warning(f"No validator found for document type '{doc_type}', using generic validation")

        validator_method = getattr(self, validator_method_name, self._validate_generic)

        logger.info(f"Validating document {document_id} (type: '{doc_type}') using {validator_method_name}")

        # Run document-type-specific validation
        type_specific_results = validator_method(doc)
        results.extend(type_specific_results)

        # Run AI anomaly detection if enabled and document has extracted data
        extracted_data = self._get_extracted_data(doc)
        if include_ai_validation and extracted_data:
            ai_results = self._validate_ai_anomaly(doc)
            results.extend(ai_results)

        # Save all results
        for result in results:
            self.db.add(result)

        # Update document status based on results
        has_failures = any(r.status == ValidationStatus.FAILED for r in results)
        has_warnings = any(r.status == ValidationStatus.WARNING for r in results)
        used_generic = self._is_generic_validation(doc)

        if has_failures:
            doc.status = DocumentStatus.EXTRACTED  # Keep as extracted, not validated
        elif used_generic or has_warnings:
            # Generic validation or warnings = needs manual review, don't mark as validated
            doc.status = DocumentStatus.EXTRACTED
            logger.info(f"Document {doc.id} needs manual review (generic={used_generic}, warnings={has_warnings})")
        else:
            doc.status = DocumentStatus.VALIDATED

        self.db.commit()

        for result in results:
            self.db.refresh(result)

        # Send email notification if validation failed
        if has_failures or has_warnings:
            try:
                import threading
                # Send email in background thread to not block validation
                thread = threading.Thread(
                    target=_send_validation_failure_email_async,
                    args=(self.db, document_id, results),
                    daemon=True
                )
                thread.start()
                logger.info(f"Queued validation failure email for document {document_id}")
            except Exception as e:
                logger.error(f"Failed to queue validation failure email: {e}", exc_info=True)

        return results

    # ========== GENERIC VALIDATION (for unknown document types) ==========
    def _validate_generic(self, doc: Document) -> list[ValidationResult]:
        """Generic validation for unknown document types.

        IMPORTANT: Generic validation always returns WARNING or FAILED status
        to ensure documents don't get marked as VALIDATED without proper review.
        """
        results = []

        doc_type_str = doc.document_type.value if doc.document_type else 'not specified'

        # Always return WARNING for generic validation - requires manual review
        results.append(ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.REQUIRED_FIELDS,
            status=ValidationStatus.WARNING,  # Never PASSED for generic
            message=f"Document type '{doc_type_str}' requires manual review",
            details="This document type does not have automated validation rules. Please review manually to ensure it meets requirements.",
            severity="medium",
            ai_reasoning={
                "validator": "GenericValidator",
                "check": "manual_review_required",
                "document_type": doc_type_str,
                "reason": "No specific validation rules for this document type",
            },
        ))

        return results

    def _is_generic_validation(self, doc: Document) -> bool:
        """Check if document will use generic validation."""
        if not doc.document_type:
            return True
        doc_type = doc.document_type.value
        return (doc_type not in self.DOCUMENT_TYPE_VALIDATORS and
                doc_type.upper() not in self.DOCUMENT_TYPE_VALIDATORS)

    # ========== INVOICE VALIDATION ==========
    def _validate_invoice(self, doc: Document) -> list[ValidationResult]:
        """Validate invoice-specific rules."""
        results = []

        # Required fields for invoices
        results.append(self._validate_invoice_required_fields(doc))
        results.append(self._validate_vat_number_format(doc))
        results.append(self._validate_date_in_period(doc))
        results.append(self._validate_invoice_totals(doc))
        results.append(self._validate_vat_rate(doc))
        results.append(self._validate_invoice_duplicate(doc))
        results.append(self._validate_currency(doc))

        return results

    def _validate_invoice_required_fields(self, doc: Document) -> ValidationResult:
        """Validate required fields for invoices."""
        required_fields = [
            ("invoice_number", doc.invoice_number, "Invoice number is required for VAT records"),
            ("invoice_date", doc.invoice_date, "Invoice date is required for VAT period allocation"),
            ("supplier_name", doc.supplier_name, "Supplier name is required for audit trail"),
            ("net_amount", doc.net_amount, "Net amount is required for VAT calculation"),
            ("vat_amount", doc.vat_amount, "VAT amount is required for VAT return"),
            ("gross_amount", doc.gross_amount, "Gross amount is required for reconciliation"),
        ]

        missing = [(name, reason) for name, value, reason in required_fields if value is None]

        if missing:
            missing_details = "; ".join([f"{name}: {reason}" for name, reason in missing])
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.REQUIRED_FIELDS,
                status=ValidationStatus.FAILED,
                message=f"Invoice missing {len(missing)} required field(s): {', '.join([m[0] for m in missing])}",
                details=missing_details,
                severity="high",
                ai_reasoning={
                    "validator": "InvoiceValidator",
                    "check": "required_fields",
                    "missing_fields": [{"field": m[0], "reason": m[1]} for m in missing],
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.REQUIRED_FIELDS,
            status=ValidationStatus.PASSED,
            message="All required invoice fields present",
        )

    def _validate_invoice_totals(self, doc: Document) -> ValidationResult:
        """Validate invoice calculation: net + VAT = gross."""
        if doc.net_amount is None or doc.vat_amount is None or doc.gross_amount is None:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.TOTALS_MATCH,
                status=ValidationStatus.SKIPPED,
                message="Missing amount fields for invoice calculation validation",
            )

        calculated_gross = doc.net_amount + doc.vat_amount
        difference = abs(calculated_gross - doc.gross_amount)

        if difference <= CALCULATION_TOLERANCE:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.TOTALS_MATCH,
                status=ValidationStatus.PASSED,
                message="Invoice calculation verified: Net + VAT = Gross",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.TOTALS_MATCH,
            status=ValidationStatus.FAILED,
            message=f"Invoice calculation error: £{doc.net_amount} + £{doc.vat_amount} = £{calculated_gross}, but invoice shows £{doc.gross_amount}",
            details=f"Difference of £{difference:.2f} detected. This may indicate a data entry error or OCR extraction issue.",
            field_name="gross_amount",
            expected_value=str(calculated_gross),
            actual_value=str(doc.gross_amount),
            severity="high",
            ai_reasoning={
                "validator": "InvoiceValidator",
                "check": "totals_match",
                "calculation": f"{doc.net_amount} + {doc.vat_amount} = {calculated_gross}",
                "difference": float(difference),
            },
        )

    def _validate_invoice_duplicate(self, doc: Document) -> ValidationResult:
        """Check for duplicate invoices."""
        if not doc.invoice_number:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DUPLICATE_DETECTION,
                status=ValidationStatus.SKIPPED,
                message="No invoice number for duplicate check",
            )

        stmt = select(Document).where(
            Document.invoice_number == doc.invoice_number,
            Document.id != doc.id,
        )
        duplicates = list(self.db.scalars(stmt).all())

        if duplicates:
            dup_info = [{"id": d.id, "filename": d.filename, "supplier": d.supplier_name} for d in duplicates]
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DUPLICATE_DETECTION,
                status=ValidationStatus.WARNING,
                message=f"Potential duplicate invoice: Invoice #{doc.invoice_number} already exists",
                details=f"Found {len(duplicates)} other document(s) with the same invoice number. Review to avoid double-counting for VAT.",
                severity="medium",
                ai_reasoning={
                    "validator": "InvoiceValidator",
                    "check": "duplicate_detection",
                    "duplicates": dup_info,
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DUPLICATE_DETECTION,
            status=ValidationStatus.PASSED,
            message="No duplicate invoices found",
        )

    # ========== BANK STATEMENT VALIDATION ==========
    def _validate_bank_statement(self, doc: Document) -> list[ValidationResult]:
        """Validate bank statement-specific rules."""
        results = []

        results.append(self._validate_bank_statement_required_fields(doc))
        results.append(self._validate_bank_statement_period(doc))
        results.append(self._validate_bank_statement_balance(doc))
        results.append(self._validate_bank_account_format(doc))

        return results

    def _validate_bank_statement_required_fields(self, doc: Document) -> ValidationResult:
        """Validate required fields for bank statements."""
        extracted = self._get_extracted_data(doc) or {}

        required_checks = [
            ("account_number", extracted.get("account_number"), "Account number needed to identify bank account"),
            ("statement_period", extracted.get("statement_period") or extracted.get("period_start"), "Statement period needed for VAT period matching"),
            ("opening_balance", extracted.get("opening_balance"), "Opening balance needed for reconciliation"),
            ("closing_balance", extracted.get("closing_balance"), "Closing balance needed for reconciliation"),
        ]

        missing = [(name, reason) for name, value, reason in required_checks if not value]

        if missing:
            missing_details = "; ".join([f"{name}: {reason}" for name, reason in missing])
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.REQUIRED_FIELDS,
                status=ValidationStatus.FAILED,
                message=f"Bank statement missing {len(missing)} required field(s): {', '.join([m[0] for m in missing])}",
                details=missing_details,
                severity="high",
                ai_reasoning={
                    "validator": "BankStatementValidator",
                    "check": "required_fields",
                    "missing_fields": [{"field": m[0], "reason": m[1]} for m in missing],
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.REQUIRED_FIELDS,
            status=ValidationStatus.PASSED,
            message="All required bank statement fields present",
        )

    def _validate_bank_statement_period(self, doc: Document) -> ValidationResult:
        """Validate bank statement period matches VAT period."""
        extracted = self._get_extracted_data(doc) or {}
        period_start = extracted.get("period_start")
        period_end = extracted.get("period_end")

        if not period_start or not period_end:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.WARNING,
                message="Bank statement period dates not extracted",
                details="Unable to verify if statement covers the correct VAT period.",
                severity="medium",
                ai_reasoning={
                    "validator": "BankStatementValidator",
                    "check": "period_coverage",
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DATE_IN_PERIOD,
            status=ValidationStatus.PASSED,
            message=f"Bank statement covers period: {period_start} to {period_end}",
        )

    def _validate_bank_statement_balance(self, doc: Document) -> ValidationResult:
        """Validate bank statement balance reconciliation."""
        extracted = self._get_extracted_data(doc) or {}
        opening = extracted.get("opening_balance")
        closing = extracted.get("closing_balance")
        total_credits = extracted.get("total_credits")
        total_debits = extracted.get("total_debits")

        if not all([opening, closing]):
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.TOTALS_MATCH,
                status=ValidationStatus.SKIPPED,
                message="Balance fields not available for reconciliation check",
            )

        result = reconcile_balances(
            opening_balance=opening,
            closing_balance=closing,
            total_credits=total_credits,
            total_debits=total_debits,
            tolerance=CALCULATION_TOLERANCE,
        )

        if result["ok"] is False:
            expected = result["expected_closing"]
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.TOTALS_MATCH,
                status=ValidationStatus.FAILED,
                message=f"Bank statement balance discrepancy: Expected closing £{expected}, actual £{closing}",
                details=f"Opening (£{opening}) + Credits (£{total_credits}) - Debits (£{total_debits}) = £{expected}, but statement shows £{closing}",
                expected_value=str(expected),
                actual_value=str(closing),
                severity="high",
                ai_reasoning={
                    "validator": "BankStatementValidator",
                    "check": "balance_reconciliation",
                    "calculation": {
                        "opening": opening,
                        "credits": total_credits,
                        "debits": total_debits,
                        "expected_closing": float(expected),
                        "actual_closing": float(result["closing"]) if result["closing"] is not None else None,
                    },
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.TOTALS_MATCH,
            status=ValidationStatus.PASSED,
            message="Bank statement balances verified",
        )

    def _validate_bank_account_format(self, doc: Document) -> ValidationResult:
        """Validate UK bank account number format."""
        extracted = self._get_extracted_data(doc) or {}
        account_number = extracted.get("account_number")
        sort_code = extracted.get("sort_code")

        issues = []

        if account_number:
            clean_account = re.sub(r'\D', '', str(account_number))
            if len(clean_account) != 8:
                issues.append(f"Account number '{account_number}' should be 8 digits (found {len(clean_account)})")

        if sort_code:
            clean_sort = re.sub(r'\D', '', str(sort_code))
            if len(clean_sort) != 6:
                issues.append(f"Sort code '{sort_code}' should be 6 digits (found {len(clean_sort)})")

        if issues:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_NUMBER_FORMAT,  # Reusing for account format
                status=ValidationStatus.WARNING,
                message="Bank account format issues detected",
                details="; ".join(issues),
                severity="low",
                ai_reasoning={
                    "validator": "BankStatementValidator",
                    "check": "account_format",
                    "issues": issues,
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_NUMBER_FORMAT,
            status=ValidationStatus.PASSED,
            message="Bank account format valid",
        )

    # ========== RECEIPT VALIDATION ==========
    def _validate_receipt(self, doc: Document) -> list[ValidationResult]:
        """Validate receipt-specific rules."""
        results = []

        results.append(self._validate_receipt_required_fields(doc))
        results.append(self._validate_receipt_date(doc))
        results.append(self._validate_receipt_vat_requirements(doc))
        results.append(self._validate_currency(doc))

        return results

    def _validate_receipt_required_fields(self, doc: Document) -> ValidationResult:
        """Validate required fields for receipts."""
        extracted = self._get_extracted_data(doc) or {}

        required_checks = [
            ("vendor_name", extracted.get("vendor_name") or doc.supplier_name, "Vendor/merchant name needed for expense categorization"),
            ("date", extracted.get("receipt_date") or doc.invoice_date, "Receipt date needed for VAT period allocation"),
            ("total_amount", extracted.get("total_amount") or doc.gross_amount, "Total amount needed for expense tracking"),
        ]

        missing = [(name, reason) for name, value, reason in required_checks if not value]

        if missing:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.REQUIRED_FIELDS,
                status=ValidationStatus.FAILED,
                message=f"Receipt missing {len(missing)} required field(s): {', '.join([m[0] for m in missing])}",
                details="; ".join([f"{name}: {reason}" for name, reason in missing]),
                severity="high",
                ai_reasoning={
                    "validator": "ReceiptValidator",
                    "check": "required_fields",
                    "missing_fields": [{"field": m[0], "reason": m[1]} for m in missing],
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.REQUIRED_FIELDS,
            status=ValidationStatus.PASSED,
            message="All required receipt fields present",
        )

    def _validate_receipt_date(self, doc: Document) -> ValidationResult:
        """Validate receipt date."""
        from datetime import datetime, timedelta

        receipt_date = doc.invoice_date
        extracted = self._get_extracted_data(doc) or {}
        if not receipt_date and extracted.get("receipt_date"):
            try:
                receipt_date = datetime.strptime(extracted["receipt_date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        if not receipt_date:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.WARNING,
                message="Receipt date not available",
                severity="medium",
            )

        # Check if receipt is too old (> 4 years for VAT claims)
        four_years_ago = (datetime.now() - timedelta(days=4*365)).date()
        if receipt_date < four_years_ago:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.FAILED,
                message=f"Receipt dated {receipt_date} is over 4 years old",
                details="HMRC only allows VAT claims on expenses within 4 years. This receipt may not be eligible for VAT recovery.",
                severity="high",
                ai_reasoning={
                    "validator": "ReceiptValidator",
                    "check": "date_validity",
                    "receipt_date": str(receipt_date),
                    "cutoff_date": str(four_years_ago),
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DATE_IN_PERIOD,
            status=ValidationStatus.PASSED,
            message="Receipt date within valid period",
        )

    def _validate_receipt_vat_requirements(self, doc: Document) -> ValidationResult:
        """Validate VAT invoice requirements for receipts over £250."""
        extracted = self._get_extracted_data(doc) or {}
        total = doc.gross_amount or extracted.get("total_amount")

        if not total:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,
                status=ValidationStatus.SKIPPED,
                message="No total amount for VAT requirements check",
            )

        try:
            total_decimal = Decimal(str(total))
        except:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,
                status=ValidationStatus.SKIPPED,
                message="Invalid total amount format",
            )

        # For receipts over £250, full VAT invoice details are required
        if total_decimal > Decimal("250"):
            vat_requirements = [
                ("supplier_vat_number", doc.supplier_vat_number or extracted.get("vat_number")),
                ("supplier_address", extracted.get("vendor_address") or extracted.get("supplier_address")),
            ]
            missing = [name for name, value in vat_requirements if not value]

            if missing:
                return ValidationResult(
                    document_id=doc.id,
                    rule_type=RuleType.VAT_RATE_VALID,
                    status=ValidationStatus.WARNING,
                    message=f"Receipt over £250 missing VAT invoice requirements: {', '.join(missing)}",
                    details="For purchases over £250, HMRC requires a full VAT invoice with supplier VAT number and address to reclaim VAT.",
                    severity="medium",
                    ai_reasoning={
                        "validator": "ReceiptValidator",
                        "check": "vat_invoice_requirements",
                        "total": float(total_decimal),
                        "threshold": 250,
                        "missing": missing,
                    },
                )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_RATE_VALID,
            status=ValidationStatus.PASSED,
            message="Receipt meets VAT requirements",
        )

    # ========== PAYROLL VALIDATION ==========
    def _validate_payroll(self, doc: Document) -> list[ValidationResult]:
        """Validate payroll-specific rules."""
        results = []

        results.append(self._validate_payroll_required_fields(doc))
        results.append(self._validate_payroll_ni_number(doc))
        results.append(self._validate_payroll_tax_code(doc))
        results.append(self._validate_payroll_calculations(doc))
        results.append(self._validate_payroll_ni_contributions(doc))
        results.append(self._validate_payroll_bank_account_match(doc))

        return results

    def _validate_payroll_bank_account_match(self, doc: Document) -> ValidationResult:
        """Validate payroll employee name matches bank account holder name."""
        extracted = self._get_extracted_data(doc) or {}
        employee_name = (
            extracted.get("employee_name")
            or extracted.get("employee_full_name")
            or extracted.get("employee")
        )

        if not employee_name:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.ACCOUNT_HOLDER_MATCH,
                status=ValidationStatus.SKIPPED,
                message="No employee name found to match against bank account",
            )

        if not doc.engagement_id:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.ACCOUNT_HOLDER_MATCH,
                status=ValidationStatus.SKIPPED,
                message="Payroll document not linked to an engagement",
            )

        # Find bank statements in the same engagement
        stmt = (
            select(Document)
            .where(
                Document.engagement_id == doc.engagement_id,
                Document.id != doc.id,
            )
            .order_by(Document.updated_at.desc())
        )
        bank_doc = None
        for candidate in self.db.scalars(stmt).all():
            extracted = self._get_extracted_data(candidate)
            if extracted and extracted.get("document_type") == "bank_statement":
                bank_doc = candidate
                break

        bank_extracted = self._get_extracted_data(bank_doc) if bank_doc else None
        if not bank_doc or not bank_extracted:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.ACCOUNT_HOLDER_MATCH,
                status=ValidationStatus.SKIPPED,
                message="No bank statement data found for this engagement",
            )

        bank_data = bank_extracted or {}
        account_holder = (
            bank_data.get("account_holder_name")
            or bank_data.get("account_name")
            or (bank_data.get("account_details") or {}).get("account_name")
        )

        if not account_holder:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.ACCOUNT_HOLDER_MATCH,
                status=ValidationStatus.SKIPPED,
                message="Bank statement missing account holder name",
            )

        if self._names_match(employee_name, account_holder):
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.ACCOUNT_HOLDER_MATCH,
                status=ValidationStatus.PASSED,
                message="Payslip employee name matches bank account holder",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.ACCOUNT_HOLDER_MATCH,
            status=ValidationStatus.WARNING,
            message="Payslip employee name does not match bank account holder",
            details=f"Employee '{employee_name}' vs account holder '{account_holder}'",
            field_name="account_holder_name",
            expected_value=str(employee_name),
            actual_value=str(account_holder),
            severity="medium",
            ai_reasoning={
                "validator": "PayrollValidator",
                "check": "employee_account_match",
                "employee_name": employee_name,
                "account_holder_name": account_holder,
            },
        )

    def _validate_payroll_required_fields(self, doc: Document) -> ValidationResult:
        """Validate required fields for payroll documents."""
        extracted = self._get_extracted_data(doc) or {}

        required_checks = [
            ("employee_name", extracted.get("employee_name"), "Employee name is required for payroll records"),
            ("pay_period", extracted.get("pay_period") or extracted.get("period"), "Pay period is required for HMRC RTI reporting"),
            ("gross_pay", extracted.get("gross_pay") or extracted.get("gross_salary"), "Gross pay is required for tax calculations"),
            ("net_pay", extracted.get("net_pay") or extracted.get("take_home_pay"), "Net pay is required for payment verification"),
            ("paye_tax", extracted.get("paye_tax") or extracted.get("income_tax") or extracted.get("tax"), "PAYE tax deduction is required"),
            ("national_insurance", extracted.get("national_insurance") or extracted.get("ni") or extracted.get("ni_employee"), "NI contribution is required"),
        ]

        missing = [(name, reason) for name, value, reason in required_checks if not value]

        if missing:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.REQUIRED_FIELDS,
                status=ValidationStatus.FAILED,
                message=f"Payroll document missing {len(missing)} required field(s): {', '.join([m[0] for m in missing])}",
                details="; ".join([f"{name}: {reason}" for name, reason in missing]),
                severity="high",
                ai_reasoning={
                    "validator": "PayrollValidator",
                    "check": "required_fields",
                    "missing_fields": [{"field": m[0], "reason": m[1]} for m in missing],
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.REQUIRED_FIELDS,
            status=ValidationStatus.PASSED,
            message="All required payroll fields present",
        )

    def _validate_payroll_ni_number(self, doc: Document) -> ValidationResult:
        """Validate National Insurance number format."""
        import re
        extracted = self._get_extracted_data(doc) or {}
        ni_number = extracted.get("ni_number") or extracted.get("national_insurance_number")

        if not ni_number:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_NUMBER_FORMAT,  # Re-using format validation type
                status=ValidationStatus.WARNING,
                message="No National Insurance number found in payroll document",
                details="NI number is required for HMRC reporting. Ensure it's included in payroll records.",
                severity="medium",
                ai_reasoning={
                    "validator": "PayrollValidator",
                    "check": "ni_number_presence",
                },
            )

        # UK NI number format: 2 letters, 6 numbers, 1 letter (e.g., AB123456C)
        ni_pattern = r"^[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$"
        cleaned = str(ni_number).upper().replace(" ", "")

        if not re.match(ni_pattern, cleaned):
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_NUMBER_FORMAT,
                status=ValidationStatus.FAILED,
                message=f"Invalid National Insurance number format: {ni_number}",
                details="UK NI numbers follow the format: 2 letters, 6 digits, 1 letter (e.g., AB123456C). Certain letter combinations are invalid.",
                field_name="ni_number",
                actual_value=ni_number,
                severity="high",
                ai_reasoning={
                    "validator": "PayrollValidator",
                    "check": "ni_number_format",
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_NUMBER_FORMAT,
            status=ValidationStatus.PASSED,
            message="National Insurance number format valid",
        )

    def _validate_payroll_tax_code(self, doc: Document) -> ValidationResult:
        """Validate tax code format."""
        import re
        extracted = self._get_extracted_data(doc) or {}
        tax_code = extracted.get("tax_code")

        if not tax_code:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,  # Re-using for tax validation
                status=ValidationStatus.WARNING,
                message="No tax code found in payroll document",
                details="Tax code should be displayed on payslips. Check if this is a complete payroll record.",
                severity="low",
            )

        tax_code_str = str(tax_code).upper().strip()

        # Common tax code patterns
        valid_patterns = [
            r"^\d{1,4}[LMNTX]$",  # Standard codes like 1257L
            r"^K\d{1,4}$",  # K codes (negative allowance)
            r"^S\d{1,4}[LMNTX]$",  # Scottish codes
            r"^C\d{1,4}[LMNTX]$",  # Welsh codes
            r"^BR$",  # Basic rate
            r"^D[01]$",  # Higher/additional rate
            r"^NT$",  # No tax
            r"^0T$",  # No allowance
        ]

        is_valid_format = any(re.match(p, tax_code_str) for p in valid_patterns)

        if not is_valid_format:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,
                status=ValidationStatus.WARNING,
                message=f"Unusual tax code format: {tax_code}",
                details="Tax code format may be incorrect. Common formats: 1257L, BR, D0, S1257L (Scotland), etc.",
                field_name="tax_code",
                actual_value=tax_code,
                severity="medium",
                ai_reasoning={
                    "validator": "PayrollValidator",
                    "check": "tax_code_format",
                },
            )

        # Check for emergency tax codes
        if tax_code_str.endswith("W1") or tax_code_str.endswith("M1") or "X" in tax_code_str:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,
                status=ValidationStatus.WARNING,
                message=f"Emergency/week 1/month 1 tax code detected: {tax_code}",
                details="Employee may be on emergency tax. Consider contacting HMRC to obtain the correct tax code.",
                field_name="tax_code",
                actual_value=tax_code,
                severity="low",
                ai_reasoning={
                    "validator": "PayrollValidator",
                    "check": "emergency_tax_code",
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_RATE_VALID,
            status=ValidationStatus.PASSED,
            message=f"Tax code {tax_code} format valid",
        )

    def _validate_payroll_calculations(self, doc: Document) -> ValidationResult:
        """Validate net pay calculation: gross - deductions = net."""
        extracted = self._get_extracted_data(doc) or {}

        gross = self._parse_amount(extracted.get("gross_pay") or extracted.get("gross_salary"))
        net = self._parse_amount(extracted.get("net_pay") or extracted.get("take_home_pay"))
        paye = self._parse_amount(extracted.get("paye_tax") or extracted.get("income_tax") or extracted.get("tax")) or Decimal("0")
        ni = self._parse_amount(extracted.get("national_insurance") or extracted.get("ni") or extracted.get("ni_employee")) or Decimal("0")
        pension = self._parse_amount(extracted.get("pension") or extracted.get("pension_employee")) or Decimal("0")
        student_loan = self._parse_amount(extracted.get("student_loan")) or Decimal("0")
        other_deductions = self._parse_amount(extracted.get("other_deductions")) or Decimal("0")

        if gross is None or net is None:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.TOTALS_MATCH,
                status=ValidationStatus.SKIPPED,
                message="Missing gross or net pay for calculation validation",
            )

        total_deductions = paye + ni + pension + student_loan + other_deductions
        expected_net = gross - total_deductions

        # Allow small tolerance for rounding
        tolerance = Decimal("0.05")
        difference = abs(expected_net - net)

        if difference > tolerance:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.TOTALS_MATCH,
                status=ValidationStatus.FAILED,
                message=f"Payroll calculation mismatch: expected net £{expected_net:.2f}, actual £{net:.2f}",
                details=f"Gross £{gross} - Deductions £{total_deductions} should equal £{expected_net}, but shows £{net}. Difference: £{difference:.2f}",
                field_name="net_pay",
                expected_value=f"£{expected_net:.2f}",
                actual_value=f"£{net:.2f}",
                severity="high",
                ai_reasoning={
                    "validator": "PayrollValidator",
                    "check": "net_pay_calculation",
                    "calculation": {
                        "gross": float(gross),
                        "paye": float(paye),
                        "ni": float(ni),
                        "pension": float(pension),
                        "student_loan": float(student_loan),
                        "other_deductions": float(other_deductions),
                        "total_deductions": float(total_deductions),
                        "expected_net": float(expected_net),
                        "actual_net": float(net),
                        "difference": float(difference),
                    },
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.TOTALS_MATCH,
            status=ValidationStatus.PASSED,
            message="Payroll calculation verified: Gross - Deductions = Net",
        )

    def _validate_payroll_ni_contributions(self, doc: Document) -> ValidationResult:
        """Validate NI contributions are reasonable for earnings."""
        extracted = self._get_extracted_data(doc) or {}

        gross = self._parse_amount(extracted.get("gross_pay") or extracted.get("gross_salary"))
        ni = self._parse_amount(extracted.get("national_insurance") or extracted.get("ni") or extracted.get("ni_employee"))

        if gross is None or ni is None:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,
                status=ValidationStatus.SKIPPED,
                message="Missing gross pay or NI for contribution validation",
            )

        # 2024/25 NI thresholds (monthly approximation)
        # Primary threshold: £1,048/month - below this, 0% NI
        # Upper earnings limit: £4,189/month
        monthly_threshold = Decimal("1048")

        if gross <= monthly_threshold:
            # Should be 0 NI
            if ni > Decimal("0.50"):
                return ValidationResult(
                    document_id=doc.id,
                    rule_type=RuleType.VAT_RATE_VALID,
                    status=ValidationStatus.WARNING,
                    message=f"NI charged on earnings below threshold: £{ni:.2f} deducted from £{gross:.2f} gross",
                    details=f"Earnings below £{monthly_threshold}/month should have zero or minimal NI. Check if this is correct.",
                    field_name="national_insurance",
                    expected_value="£0.00 (below threshold)",
                    actual_value=f"£{ni:.2f}",
                    severity="medium",
                    ai_reasoning={
                        "validator": "PayrollValidator",
                        "check": "ni_threshold",
                        "gross": float(gross),
                        "ni": float(ni),
                        "threshold": float(monthly_threshold),
                    },
                )
        elif ni == Decimal("0") and gross > monthly_threshold:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_RATE_VALID,
                status=ValidationStatus.WARNING,
                message=f"No NI contributions on earnings of £{gross:.2f}",
                details="Unless employee is exempt (e.g., over state pension age), NI should be deducted on earnings above threshold.",
                field_name="national_insurance",
                expected_value="NI contribution expected",
                actual_value="£0.00",
                severity="medium",
                ai_reasoning={
                    "validator": "PayrollValidator",
                    "check": "ni_missing",
                    "gross": float(gross),
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_RATE_VALID,
            status=ValidationStatus.PASSED,
            message="NI contributions appear reasonable for earnings level",
        )

    def _parse_amount(self, value: Any) -> Decimal | None:
        """Parse amount value to Decimal."""
        if value is None:
            return None
        try:
            if isinstance(value, Decimal):
                return value
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            if isinstance(value, str):
                cleaned = value.replace("£", "").replace("$", "").replace(",", "").strip()
                return Decimal(cleaned)
            return Decimal(str(value))
        except:
            return None

    # ========== VAT CERTIFICATE VALIDATION ==========
    def _validate_vat_certificate(self, doc: Document) -> list[ValidationResult]:
        """Validate VAT certificate-specific rules."""
        results = []

        results.append(self._validate_vat_cert_required_fields(doc))
        results.append(self._validate_vat_cert_number(doc))
        results.append(self._validate_vat_cert_date(doc))

        return results

    def _validate_vat_cert_required_fields(self, doc: Document) -> ValidationResult:
        """Validate required fields for VAT certificates."""
        extracted = self._get_extracted_data(doc) or {}

        required_checks = [
            ("vat_number", extracted.get("vat_number") or doc.supplier_vat_number, "VAT registration number is the primary identifier"),
            ("business_name", extracted.get("business_name") or doc.supplier_name, "Business name needed to verify registration"),
            ("effective_date", extracted.get("effective_date") or extracted.get("registration_date"), "Effective date shows when VAT registration began"),
        ]

        missing = [(name, reason) for name, value, reason in required_checks if not value]

        if missing:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.REQUIRED_FIELDS,
                status=ValidationStatus.FAILED,
                message=f"VAT certificate missing {len(missing)} required field(s): {', '.join([m[0] for m in missing])}",
                details="; ".join([f"{name}: {reason}" for name, reason in missing]),
                severity="high",
                ai_reasoning={
                    "validator": "VATCertificateValidator",
                    "check": "required_fields",
                    "missing_fields": [{"field": m[0], "reason": m[1]} for m in missing],
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.REQUIRED_FIELDS,
            status=ValidationStatus.PASSED,
            message="All required VAT certificate fields present",
        )

    def _validate_vat_cert_number(self, doc: Document) -> ValidationResult:
        """Validate VAT number format on certificate."""
        extracted = self._get_extracted_data(doc) or {}
        vat_number = extracted.get("vat_number") or doc.supplier_vat_number

        if not vat_number:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_NUMBER_FORMAT,
                status=ValidationStatus.FAILED,
                message="VAT certificate has no VAT number",
                severity="high",
            )

        # UK VAT number: GB followed by 9 or 12 digits
        clean_vat = re.sub(r'\s', '', str(vat_number).upper())

        if clean_vat.startswith("GB"):
            digits = clean_vat[2:]
        else:
            digits = clean_vat

        if not (len(digits) == 9 or len(digits) == 12) or not digits.isdigit():
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.VAT_NUMBER_FORMAT,
                status=ValidationStatus.FAILED,
                message=f"Invalid VAT number format: '{vat_number}'",
                details="UK VAT numbers must be 'GB' followed by 9 or 12 digits. Verify this certificate with HMRC's online checker.",
                expected_value="GB followed by 9 or 12 digits",
                actual_value=vat_number,
                severity="high",
                ai_reasoning={
                    "validator": "VATCertificateValidator",
                    "check": "vat_number_format",
                    "vat_number": vat_number,
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_NUMBER_FORMAT,
            status=ValidationStatus.PASSED,
            message=f"VAT number format valid: {vat_number}",
        )

    def _validate_vat_cert_date(self, doc: Document) -> ValidationResult:
        """Validate VAT certificate effective date."""
        from datetime import datetime

        extracted = self._get_extracted_data(doc) or {}
        effective_date_str = extracted.get("effective_date") or extracted.get("registration_date")

        if not effective_date_str:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.WARNING,
                message="VAT certificate effective date not found",
                severity="medium",
            )

        # Try to parse the date
        effective_date = None
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                effective_date = datetime.strptime(str(effective_date_str), fmt)
                break
            except ValueError:
                continue

        if not effective_date:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.WARNING,
                message=f"Could not parse effective date: {effective_date_str}",
                severity="low",
            )

        # Check if in the future
        if effective_date > datetime.now():
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.FAILED,
                message=f"VAT certificate effective date is in the future: {effective_date_str}",
                details="VAT registration effective dates should not be in the future. This may indicate an invalid or fraudulent certificate.",
                severity="high",
                ai_reasoning={
                    "validator": "VATCertificateValidator",
                    "check": "effective_date",
                    "date": effective_date_str,
                },
            )

        # Check if before UK VAT system (1973)
        if effective_date.year < 1973:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.FAILED,
                message=f"VAT certificate date {effective_date_str} is before UK VAT system began (1973)",
                severity="high",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DATE_IN_PERIOD,
            status=ValidationStatus.PASSED,
            message=f"VAT certificate effective date valid: {effective_date_str}",
        )

    # ========== CONTRACT VALIDATION ==========
    def _validate_contract(self, doc: Document) -> list[ValidationResult]:
        """Validate contract-specific rules."""
        results = []

        results.append(self._validate_contract_required_fields(doc))
        results.append(self._validate_contract_parties(doc))
        results.append(self._validate_contract_dates(doc))
        results.append(self._validate_contract_vat_treatment(doc))

        return results

    def _validate_contract_required_fields(self, doc: Document) -> ValidationResult:
        """Validate required fields for contracts."""
        extracted = self._get_extracted_data(doc) or {}

        required_checks = [
            ("party_1", extracted.get("party_1_name") or extracted.get("party_1"), "First party name needed to identify contractual relationship"),
            ("party_2", extracted.get("party_2_name") or extracted.get("party_2"), "Second party name needed to identify contractual relationship"),
            ("contract_date", extracted.get("contract_date") or extracted.get("effective_date"), "Contract date needed for determining VAT liability"),
        ]

        missing = [(name, reason) for name, value, reason in required_checks if not value]

        if missing:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.REQUIRED_FIELDS,
                status=ValidationStatus.FAILED,
                message=f"Contract missing {len(missing)} required field(s): {', '.join([m[0] for m in missing])}",
                details="; ".join([f"{name}: {reason}" for name, reason in missing]),
                severity="high",
                ai_reasoning={
                    "validator": "ContractValidator",
                    "check": "required_fields",
                    "missing_fields": [{"field": m[0], "reason": m[1]} for m in missing],
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.REQUIRED_FIELDS,
            status=ValidationStatus.PASSED,
            message="All required contract fields present",
        )

    def _validate_contract_parties(self, doc: Document) -> ValidationResult:
        """Validate contract parties are distinct."""
        extracted = self._get_extracted_data(doc) or {}
        party_1 = extracted.get("party_1_name") or extracted.get("party_1") or ""
        party_2 = extracted.get("party_2_name") or extracted.get("party_2") or ""

        if party_1 and party_2:
            if party_1.lower().strip() == party_2.lower().strip():
                return ValidationResult(
                    document_id=doc.id,
                    rule_type=RuleType.DUPLICATE_DETECTION,
                    status=ValidationStatus.FAILED,
                    message="Contract parties appear to be the same entity",
                    details=f"Both parties are listed as '{party_1}'. A valid contract requires two distinct parties.",
                    severity="high",
                    ai_reasoning={
                        "validator": "ContractValidator",
                        "check": "party_distinction",
                        "party_1": party_1,
                        "party_2": party_2,
                    },
                )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DUPLICATE_DETECTION,
            status=ValidationStatus.PASSED,
            message="Contract parties are distinct",
        )

    def _validate_contract_dates(self, doc: Document) -> ValidationResult:
        """Validate contract dates are logical."""
        from datetime import datetime

        extracted = self._get_extracted_data(doc) or {}
        start_date_str = extracted.get("start_date")
        end_date_str = extracted.get("end_date")

        if not start_date_str or not end_date_str:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.SKIPPED,
                message="Contract start/end dates not available",
            )

        # Try to parse dates
        start_date = end_date = None
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                if not start_date:
                    start_date = datetime.strptime(str(start_date_str), fmt)
                if not end_date:
                    end_date = datetime.strptime(str(end_date_str), fmt)
            except ValueError:
                continue

        if start_date and end_date and end_date < start_date:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.FAILED,
                message=f"Contract end date ({end_date_str}) is before start date ({start_date_str})",
                details="Contract period is invalid. End date must be after start date.",
                expected_value=f"End date after {start_date_str}",
                actual_value=end_date_str,
                severity="high",
                ai_reasoning={
                    "validator": "ContractValidator",
                    "check": "date_logic",
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                },
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DATE_IN_PERIOD,
            status=ValidationStatus.PASSED,
            message="Contract dates are valid",
        )

    def _validate_contract_vat_treatment(self, doc: Document) -> ValidationResult:
        """Check if contract specifies VAT treatment."""
        extracted = self._get_extracted_data(doc) or {}
        contract_value = extracted.get("contract_value")
        vat_inclusive = extracted.get("vat_inclusive")
        vat_mentioned = extracted.get("vat_rate") or extracted.get("vat_amount")

        # Only flag if contract has significant value
        if contract_value:
            try:
                value = Decimal(str(contract_value).replace("£", "").replace(",", ""))
                if value > Decimal("1000") and vat_inclusive is None and not vat_mentioned:
                    return ValidationResult(
                        document_id=doc.id,
                        rule_type=RuleType.VAT_RATE_VALID,
                        status=ValidationStatus.WARNING,
                        message=f"Contract value £{value:,.2f} does not specify VAT treatment",
                        details="For VAT compliance, contracts should clearly state whether prices include or exclude VAT. This affects VAT point calculations.",
                        severity="medium",
                        ai_reasoning={
                            "validator": "ContractValidator",
                            "check": "vat_treatment",
                            "contract_value": float(value),
                        },
                    )
            except (ValueError, TypeError):
                pass

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.VAT_RATE_VALID,
            status=ValidationStatus.PASSED,
            message="Contract VAT treatment check complete",
        )

    def _validate_ai_anomaly(self, doc: Document) -> list[ValidationResult]:
        """Run AI anomaly detection using specialized document agents.

        Uses the AgentRegistry to select the appropriate specialized agent
        based on document type. Each agent has domain-specific knowledge
        for better verification accuracy.

        Returns a list of ValidationResult objects for each anomaly detected.
        """
        extracted_data = self._get_extracted_data(doc)
        if not extracted_data:
            return [
                ValidationResult(
                    document_id=doc.id,
                    rule_type=RuleType.AI_ANOMALY,
                    status=ValidationStatus.SKIPPED,
                    message="No extracted data available for AI validation",
                )
            ]

        try:
            # Get document type
            document_type = doc.document_type.value if doc.document_type else "INVOICE"

            # Create agent registry with AI provider
            registry = AgentRegistry(self.ai_provider)

            # Log which agent is being used
            agent = registry.get_agent(document_type)
            logger.info(
                f"Using {agent.__class__.__name__} for document {doc.id} (type: {document_type})"
            )

            # Run async verification in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                verification_result = loop.run_until_complete(
                    registry.verify_document(document_type, extracted_data)
                )
            finally:
                loop.close()

            results = []

            # Convert agent result to ValidationResult objects
            if verification_result.is_valid and not verification_result.anomalies:
                # No anomalies found - document passes AI check
                return [
                    ValidationResult(
                        document_id=doc.id,
                        rule_type=RuleType.AI_ANOMALY,
                        status=ValidationStatus.PASSED,
                        message="No anomalies detected",
                        details=verification_result.summary,
                        confidence=Decimal(str(verification_result.confidence_score)),
                        ai_reasoning={
                            "is_valid": verification_result.is_valid,
                            "summary": verification_result.summary,
                            "anomalies": [],
                            "confidence_score": verification_result.confidence_score,
                            "agent_type": agent.__class__.__name__,
                            "document_type": verification_result.document_type,
                        },
                    )
                ]

            # Create a validation result for each anomaly
            for anomaly in verification_result.anomalies:
                # Map agent severity to validation status
                if anomaly.severity == AgentSeverity.HIGH:
                    status = ValidationStatus.FAILED
                elif anomaly.severity == AgentSeverity.MEDIUM:
                    status = ValidationStatus.WARNING
                else:
                    status = ValidationStatus.WARNING

                results.append(
                    ValidationResult(
                        document_id=doc.id,
                        rule_type=RuleType.AI_ANOMALY,
                        status=status,
                        message=anomaly.issue,
                        details=anomaly.suggestion,
                        field_name=anomaly.field,
                        expected_value=anomaly.expected_value,
                        actual_value=anomaly.actual_value,
                        severity=anomaly.severity.value,
                        confidence=Decimal(str(verification_result.confidence_score)),
                        ai_reasoning={
                            "anomaly": anomaly.to_dict(),
                            "summary": verification_result.summary,
                            "confidence_score": verification_result.confidence_score,
                            "is_valid": verification_result.is_valid,
                            "agent_type": agent.__class__.__name__,
                            "document_type": verification_result.document_type,
                        },
                    )
                )

            return results if results else [
                ValidationResult(
                    document_id=doc.id,
                    rule_type=RuleType.AI_ANOMALY,
                    status=ValidationStatus.PASSED,
                    message="AI validation completed with no significant issues",
                    confidence=Decimal(str(verification_result.confidence_score)),
                    ai_reasoning={
                        "agent_type": agent.__class__.__name__,
                        "document_type": verification_result.document_type,
                    },
                )
            ]

        except Exception as e:
            logger.error(f"AI anomaly detection failed for document {doc.id}: {e}")
            return [
                ValidationResult(
                    document_id=doc.id,
                    rule_type=RuleType.AI_ANOMALY,
                    status=ValidationStatus.SKIPPED,
                    message=f"AI validation failed: {str(e)}",
                    details="Manual review recommended",
                )
            ]

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

        if not doc.engagement_id:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.SKIPPED,
                message="Document not linked to engagement",
            )

        engagement = self.db.get(Engagement, doc.engagement_id)
        if not engagement:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.SKIPPED,
                message="Engagement not found",
            )

        if engagement.period_start <= doc.invoice_date <= engagement.period_end:
            return ValidationResult(
                document_id=doc.id,
                rule_type=RuleType.DATE_IN_PERIOD,
                status=ValidationStatus.PASSED,
                message="Invoice date within engagement period",
            )

        return ValidationResult(
            document_id=doc.id,
            rule_type=RuleType.DATE_IN_PERIOD,
            status=ValidationStatus.FAILED,
            message=f"Invoice date {doc.invoice_date} outside engagement period "
            f"({engagement.period_start} - {engagement.period_end})",
            field_name="invoice_date",
            expected_value=f"{engagement.period_start} - {engagement.period_end}",
            actual_value=str(doc.invoice_date),
        )

    def _normalize_name(self, name: str | None) -> list[str]:
        if not name:
            return []
        cleaned = re.sub(r"[^a-z0-9\s]", " ", str(name).lower())
        tokens = [t for t in cleaned.split() if t]
        titles = {"mr", "mrs", "ms", "miss", "dr", "sir", "madam", "prof"}
        return [t for t in tokens if t not in titles]

    def _names_match(self, name_a: str | None, name_b: str | None) -> bool:
        tokens_a = set(self._normalize_name(name_a))
        tokens_b = set(self._normalize_name(name_b))
        if not tokens_a or not tokens_b:
            return False
        if tokens_a.issubset(tokens_b) or tokens_b.issubset(tokens_a):
            return True
        common = tokens_a & tokens_b
        return len(common) >= 2

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

    def get_validation_summary(self, engagement_id: int) -> dict:
        """Get validation summary for an engagement."""
        # Get all documents for the engagement
        stmt = select(Document).where(Document.engagement_id == engagement_id)
        documents = list(self.db.scalars(stmt).all())

        total_docs = len(documents)
        validated_docs = sum(1 for d in documents if d.status == DocumentStatus.VALIDATED)
        failed_docs = sum(1 for d in documents if d.status == DocumentStatus.FAILED)
        pending_docs = sum(
            1
            for d in documents
            if d.status in [DocumentStatus.PENDING, DocumentStatus.PROCESSING]
        )

        # Get all validation results for the engagement
        all_results = []
        for doc in documents:
            results = self.get_validation_results(doc.id)
            all_results.extend(results)

        passed = sum(1 for r in all_results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in all_results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in all_results if r.status == ValidationStatus.WARNING)

        return {
            "engagement_id": engagement_id,
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
