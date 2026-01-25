"""Invoice verification agent for sales and purchase invoices."""

from decimal import Decimal, InvalidOperation
from typing import Any

from .base import Anomaly, BaseDocumentAgent, Severity, VerificationResult


class InvoiceVerificationAgent(BaseDocumentAgent):
    """Specialized agent for verifying invoices (sales and purchase).

    This agent checks:
    - Required fields (invoice number, date, amounts, VAT)
    - VAT calculation accuracy (net + VAT = gross)
    - VAT rate validity (standard UK rates: 0%, 5%, 20%)
    - Date format and validity
    - Supplier/customer information completeness
    - Line item consistency
    """

    @property
    def document_type(self) -> str:
        return "INVOICE"

    @property
    def required_fields(self) -> list[str]:
        return [
            "invoice_number",
            "invoice_date",
            "supplier_name",
            "net_amount",
            "vat_amount",
            "gross_amount",
        ]

    # Valid UK VAT rates
    VALID_VAT_RATES = [Decimal("0"), Decimal("5"), Decimal("20")]
    # Tolerance for calculation differences (handles rounding)
    CALCULATION_TOLERANCE = Decimal("0.02")

    def get_system_prompt(self) -> str:
        return """You are an expert UK VAT invoice verification specialist. Your role is to meticulously analyze invoices for compliance with UK VAT regulations and accounting standards.

You have deep knowledge of:
- UK VAT rates (Standard 20%, Reduced 5%, Zero 0%)
- Invoice requirements under UK law
- Common invoice fraud patterns and errors
- VAT calculation methods and rounding rules

When analyzing an invoice, you must verify:
1. All mandatory fields are present and correctly formatted
2. VAT calculations are mathematically correct (Net + VAT = Gross)
3. VAT rates applied are valid for the goods/services
4. Dates are logical and within expected ranges
5. Supplier information is complete (name, address, VAT number if applicable)
6. Invoice numbers follow expected patterns
7. Line items sum correctly to totals
8. Currency is consistent throughout

Be especially vigilant for:
- Calculation errors in VAT amounts
- Missing or invalid VAT registration numbers
- Duplicate invoice numbers
- Dates outside the VAT period
- Unusual rounding patterns that might indicate manipulation"""

    def get_validation_prompt(self, extracted_data: dict[str, Any]) -> str:
        return f"""Analyze this invoice data for anomalies and compliance issues:

EXTRACTED INVOICE DATA:
{self._format_data(extracted_data)}

Perform a thorough verification checking:
1. Are all required fields present? (invoice number, date, supplier, amounts)
2. Is the VAT calculation correct? (Net + VAT should equal Gross)
3. Is the VAT rate valid for UK? (0%, 5%, or 20%)
4. Are the dates reasonable and properly formatted?
5. Is the supplier information complete?
6. Do line items (if present) sum to the totals?
7. Are there any signs of data entry errors or manipulation?

Respond with a JSON object in this exact format:
{{
    "is_valid": true/false,
    "confidence_score": 0.0-1.0,
    "anomalies": [
        {{
            "field": "field_name",
            "issue": "description of the issue",
            "severity": "high|medium|low",
            "suggestion": "how to resolve",
            "expected_value": "what was expected (if applicable)",
            "actual_value": "what was found (if applicable)"
        }}
    ],
    "summary": "Brief overall assessment",
    "vat_calculation_verified": true/false,
    "line_items_verified": true/false
}}"""

    def _format_data(self, data: dict[str, Any]) -> str:
        """Format extracted data for the prompt."""
        lines = []
        for key, value in data.items():
            if value is not None:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No data extracted"

    async def verify(self, extracted_data: dict[str, Any]) -> VerificationResult:
        """Verify an invoice document.

        Args:
            extracted_data: Dictionary containing extracted invoice fields

        Returns:
            VerificationResult with detailed findings
        """
        anomalies = []

        # 1. Check required fields
        anomalies.extend(self.check_required_fields(extracted_data))

        # 2. Verify VAT calculations
        vat_anomalies = self._verify_vat_calculation(extracted_data)
        anomalies.extend(vat_anomalies)

        # 3. Verify VAT rate
        rate_anomalies = self._verify_vat_rate(extracted_data)
        anomalies.extend(rate_anomalies)

        # 4. Verify dates
        date_anomalies = self._verify_dates(extracted_data)
        anomalies.extend(date_anomalies)

        # 5. Call AI for deeper analysis
        ai_result = await self._call_ai_verification(extracted_data)
        if ai_result.get("anomalies"):
            for a in ai_result["anomalies"]:
                # Avoid duplicates
                if not any(existing.field == a.get("field") and existing.issue == a.get("issue") for existing in anomalies):
                    anomalies.append(Anomaly(
                        field=a.get("field", "unknown"),
                        issue=a.get("issue", "Unknown issue"),
                        severity=Severity(a.get("severity", "medium")),
                        suggestion=a.get("suggestion", "Review manually"),
                        expected_value=a.get("expected_value"),
                        actual_value=a.get("actual_value"),
                    ))

        # Determine overall validity
        has_high_severity = any(a.severity == Severity.HIGH for a in anomalies)
        is_valid = not has_high_severity and len(anomalies) <= 2

        # Calculate confidence
        confidence = ai_result.get("confidence_score", 0.8)
        if has_high_severity:
            confidence = min(confidence, 0.3)
        elif anomalies:
            confidence = min(confidence, 0.7)

        return VerificationResult(
            is_valid=is_valid,
            confidence_score=confidence,
            anomalies=anomalies,
            summary=ai_result.get("summary", self._generate_summary(anomalies)),
            document_type=self.document_type,
            extracted_fields=extracted_data,
        )

    def _verify_vat_calculation(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify VAT calculation: Net + VAT = Gross."""
        anomalies = []

        try:
            net = self._to_decimal(data.get("net_amount"))
            vat = self._to_decimal(data.get("vat_amount"))
            gross = self._to_decimal(data.get("gross_amount"))

            if net is not None and vat is not None and gross is not None:
                expected_gross = net + vat
                difference = abs(expected_gross - gross)

                if difference > self.CALCULATION_TOLERANCE:
                    anomalies.append(Anomaly(
                        field="gross_amount",
                        issue=f"VAT calculation mismatch: Net ({net}) + VAT ({vat}) = {expected_gross}, but Gross shows {gross}",
                        severity=Severity.HIGH,
                        suggestion="Verify the invoice amounts. The difference may indicate a data entry error or potential manipulation.",
                        expected_value=str(expected_gross),
                        actual_value=str(gross),
                    ))
        except (InvalidOperation, TypeError, ValueError):
            pass  # Skip if amounts can't be parsed

        return anomalies

    def _verify_vat_rate(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify VAT rate is valid for UK."""
        anomalies = []

        try:
            net = self._to_decimal(data.get("net_amount"))
            vat = self._to_decimal(data.get("vat_amount"))

            if net is not None and vat is not None and net > 0:
                calculated_rate = (vat / net * 100).quantize(Decimal("0.1"))

                # Check if rate matches any valid UK rate
                valid_rates = [Decimal("0"), Decimal("5"), Decimal("20")]
                rate_matches = any(
                    abs(calculated_rate - rate) <= Decimal("0.5")
                    for rate in valid_rates
                )

                if not rate_matches:
                    anomalies.append(Anomaly(
                        field="vat_rate",
                        issue=f"Calculated VAT rate ({calculated_rate}%) doesn't match standard UK VAT rates (0%, 5%, 20%)",
                        severity=Severity.MEDIUM,
                        suggestion="Verify the VAT rate applied. Non-standard rates may indicate an error or require justification.",
                        expected_value="0%, 5%, or 20%",
                        actual_value=f"{calculated_rate}%",
                    ))
        except (InvalidOperation, TypeError, ValueError, ZeroDivisionError):
            pass

        return anomalies

    def _verify_dates(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify invoice dates are reasonable."""
        from datetime import datetime, timedelta

        anomalies = []
        invoice_date = data.get("invoice_date")

        if invoice_date:
            try:
                # Try to parse date
                if isinstance(invoice_date, str):
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                        try:
                            parsed_date = datetime.strptime(invoice_date, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        anomalies.append(Anomaly(
                            field="invoice_date",
                            issue="Invoice date format is non-standard or invalid",
                            severity=Severity.LOW,
                            suggestion="Ensure date is in a standard format (YYYY-MM-DD or DD/MM/YYYY)",
                        ))
                        return anomalies

                    # Check if date is in the future
                    if parsed_date > datetime.now():
                        anomalies.append(Anomaly(
                            field="invoice_date",
                            issue="Invoice date is in the future",
                            severity=Severity.HIGH,
                            suggestion="Future-dated invoices are unusual. Verify the date is correct.",
                            actual_value=invoice_date,
                        ))

                    # Check if date is very old (more than 2 years)
                    if parsed_date < datetime.now() - timedelta(days=730):
                        anomalies.append(Anomaly(
                            field="invoice_date",
                            issue="Invoice date is more than 2 years old",
                            severity=Severity.MEDIUM,
                            suggestion="Very old invoices may be outside the VAT reclaim period. Verify if this is intentional.",
                            actual_value=invoice_date,
                        ))
            except Exception:
                pass

        return anomalies

    async def _call_ai_verification(self, data: dict[str, Any]) -> dict[str, Any]:
        """Call AI provider for deeper verification."""
        try:
            result = await self.ai_provider.validate_document(
                extracted_data=data,
                document_type=self.document_type,
            )
            return result
        except Exception as e:
            return {
                "is_valid": True,
                "confidence_score": 0.5,
                "anomalies": [],
                "summary": f"AI verification unavailable: {str(e)}",
            }

    def _to_decimal(self, value: Any) -> Decimal | None:
        """Convert value to Decimal, handling various formats."""
        if value is None:
            return None
        try:
            if isinstance(value, Decimal):
                return value
            # Remove currency symbols and commas
            if isinstance(value, str):
                cleaned = value.replace("£", "").replace("$", "").replace(",", "").strip()
                return Decimal(cleaned)
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def _generate_summary(self, anomalies: list[Anomaly]) -> str:
        """Generate a summary based on anomalies found."""
        if not anomalies:
            return "Invoice verification passed. All checks completed successfully."

        high_count = sum(1 for a in anomalies if a.severity == Severity.HIGH)
        medium_count = sum(1 for a in anomalies if a.severity == Severity.MEDIUM)

        if high_count > 0:
            return f"Invoice has {high_count} critical issue(s) requiring immediate attention."
        elif medium_count > 0:
            return f"Invoice has {medium_count} issue(s) that should be reviewed."
        else:
            return f"Invoice has {len(anomalies)} minor issue(s) noted."
