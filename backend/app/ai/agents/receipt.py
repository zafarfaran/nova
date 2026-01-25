"""Receipt verification agent."""

from decimal import Decimal, InvalidOperation
from typing import Any

from .base import Anomaly, BaseDocumentAgent, Severity, VerificationResult


class ReceiptVerificationAgent(BaseDocumentAgent):
    """Specialized agent for verifying receipts.

    This agent checks:
    - Required fields (vendor, date, amount)
    - VAT information (if applicable)
    - Receipt validity for VAT reclaim
    - Date and amount reasonableness
    - Vendor information completeness
    """

    @property
    def document_type(self) -> str:
        return "RECEIPT"

    @property
    def required_fields(self) -> list[str]:
        return [
            "vendor_name",
            "receipt_date",
            "total_amount",
        ]

    # Threshold for simplified VAT invoice (no VAT breakdown required)
    SIMPLIFIED_INVOICE_THRESHOLD = Decimal("250")

    def get_system_prompt(self) -> str:
        return """You are an expert receipt verification specialist for UK VAT compliance. Your role is to analyze receipts and determine their validity for VAT reclaim purposes.

You have deep knowledge of:
- UK VAT receipt requirements
- Simplified vs full VAT invoice rules
- What receipts can be used for VAT reclaim
- Common receipt fraud patterns
- HMRC requirements for receipt retention

When analyzing a receipt, you must verify:
1. Vendor/supplier name is clearly visible
2. Date of purchase is present and readable
3. Total amount is clear
4. For receipts over £250, full VAT invoice details are needed
5. VAT amount or rate is shown (if claiming VAT)
6. Payment method is identifiable (if visible)
7. Description of goods/services purchased

Be especially vigilant for:
- Missing or illegible dates
- Receipts over £250 without full VAT details
- Personal purchases disguised as business expenses
- Duplicate receipts
- Receipts from suspicious or unfamiliar vendors
- Cash purchases without proper documentation"""

    def get_validation_prompt(self, extracted_data: dict[str, Any]) -> str:
        return f"""Analyze this receipt data for anomalies and VAT compliance:

EXTRACTED RECEIPT DATA:
{self._format_data(extracted_data)}

Perform a thorough verification checking:
1. Is the vendor name clear and identifiable?
2. Is the date present and reasonable?
3. Is the total amount clearly stated?
4. If amount is over £250, are full VAT invoice details present?
5. Is VAT information included (if this is a VAT-registered business)?
6. Is the purchase description clear enough for categorization?
7. Does this appear to be a legitimate business expense?

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
    "vat_reclaimable": true/false,
    "requires_full_vat_invoice": true/false,
    "expense_category": "suggested category"
}}"""

    def _format_data(self, data: dict[str, Any]) -> str:
        """Format extracted data for the prompt."""
        lines = []
        for key, value in data.items():
            if value is not None:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No data extracted"

    async def verify(self, extracted_data: dict[str, Any]) -> VerificationResult:
        """Verify a receipt document.

        Args:
            extracted_data: Dictionary containing extracted receipt fields

        Returns:
            VerificationResult with detailed findings
        """
        anomalies = []

        # 1. Check required fields
        anomalies.extend(self.check_required_fields(extracted_data))

        # 2. Check if full VAT invoice is required (over £250)
        vat_anomalies = self._check_vat_invoice_requirements(extracted_data)
        anomalies.extend(vat_anomalies)

        # 3. Verify date
        date_anomalies = self._verify_date(extracted_data)
        anomalies.extend(date_anomalies)

        # 4. Verify amount reasonableness
        amount_anomalies = self._verify_amount(extracted_data)
        anomalies.extend(amount_anomalies)

        # 5. Call AI for deeper analysis
        ai_result = await self._call_ai_verification(extracted_data)
        if ai_result.get("anomalies"):
            for a in ai_result["anomalies"]:
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

    def _check_vat_invoice_requirements(self, data: dict[str, Any]) -> list[Anomaly]:
        """Check if receipt meets VAT invoice requirements based on amount."""
        anomalies = []

        total = self._to_decimal(data.get("total_amount"))

        if total is not None and total > self.SIMPLIFIED_INVOICE_THRESHOLD:
            # For receipts over £250, full VAT invoice details are required
            required_for_full = ["supplier_vat_number", "vat_amount"]
            missing = []

            for field in required_for_full:
                if not data.get(field):
                    missing.append(field)

            if missing:
                anomalies.append(Anomaly(
                    field="vat_details",
                    issue=f"Receipt over £250 requires full VAT invoice details. Missing: {', '.join(missing)}",
                    severity=Severity.HIGH,
                    suggestion="For purchases over £250, you need a full VAT invoice with supplier VAT number and VAT breakdown to reclaim VAT.",
                    expected_value="Full VAT invoice details",
                    actual_value=f"Missing: {', '.join(missing)}",
                ))

        return anomalies

    def _verify_date(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify receipt date is reasonable."""
        from datetime import datetime, timedelta

        anomalies = []
        receipt_date = data.get("receipt_date")

        if receipt_date:
            parsed = self._parse_date(receipt_date)
            if parsed:
                # Check if date is in the future
                if parsed > datetime.now():
                    anomalies.append(Anomaly(
                        field="receipt_date",
                        issue="Receipt date is in the future",
                        severity=Severity.HIGH,
                        suggestion="Verify the receipt date is correct.",
                        actual_value=str(receipt_date),
                    ))

                # Check if receipt is very old (more than 4 years - VAT reclaim limit)
                if parsed < datetime.now() - timedelta(days=1461):
                    anomalies.append(Anomaly(
                        field="receipt_date",
                        issue="Receipt is more than 4 years old - may be outside VAT reclaim period",
                        severity=Severity.MEDIUM,
                        suggestion="VAT can typically only be reclaimed within 4 years. Verify if this receipt is still valid for reclaim.",
                        actual_value=str(receipt_date),
                    ))

        return anomalies

    def _verify_amount(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify amount is reasonable."""
        anomalies = []

        total = self._to_decimal(data.get("total_amount"))

        if total is not None:
            # Check for zero or negative amounts
            if total <= 0:
                anomalies.append(Anomaly(
                    field="total_amount",
                    issue="Receipt total is zero or negative",
                    severity=Severity.HIGH,
                    suggestion="Verify the amount is correct. Zero or negative amounts are unusual.",
                    actual_value=str(total),
                ))

            # Check for unusually large amounts (might need additional verification)
            if total > Decimal("10000"):
                anomalies.append(Anomaly(
                    field="total_amount",
                    issue="Receipt total is unusually large (over £10,000)",
                    severity=Severity.LOW,
                    suggestion="Large purchases should have corresponding purchase orders or contracts for audit trail.",
                    actual_value=str(total),
                ))

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
        """Convert value to Decimal."""
        if value is None:
            return None
        try:
            if isinstance(value, Decimal):
                return value
            if isinstance(value, str):
                cleaned = value.replace("£", "").replace("$", "").replace(",", "").strip()
                return Decimal(cleaned)
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def _parse_date(self, date_str: str) -> "datetime | None":
        """Parse date string to datetime."""
        from datetime import datetime

        if not date_str:
            return None

        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"]:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        return None

    def _generate_summary(self, anomalies: list[Anomaly]) -> str:
        """Generate a summary based on anomalies found."""
        if not anomalies:
            return "Receipt verification passed. Valid for records."

        high_count = sum(1 for a in anomalies if a.severity == Severity.HIGH)
        medium_count = sum(1 for a in anomalies if a.severity == Severity.MEDIUM)

        if high_count > 0:
            return f"Receipt has {high_count} critical issue(s) - may not be valid for VAT reclaim."
        elif medium_count > 0:
            return f"Receipt has {medium_count} issue(s) to review."
        else:
            return f"Receipt has {len(anomalies)} minor observation(s)."
