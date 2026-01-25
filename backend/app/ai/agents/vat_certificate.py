"""VAT Certificate verification agent."""

import re
from typing import Any

from .base import Anomaly, BaseDocumentAgent, Severity, VerificationResult


class VATCertificateVerificationAgent(BaseDocumentAgent):
    """Specialized agent for verifying VAT registration certificates.

    This agent checks:
    - VAT number format and validity
    - Business name consistency
    - Registration date
    - Effective date of registration
    - Certificate authenticity indicators
    """

    @property
    def document_type(self) -> str:
        return "VAT_CERTIFICATE"

    @property
    def required_fields(self) -> list[str]:
        return [
            "vat_number",
            "business_name",
            "effective_date",
        ]

    # UK VAT number format: GB followed by 9 or 12 digits
    UK_VAT_PATTERN = re.compile(r'^GB\s?(\d{3}\s?\d{4}\s?\d{2}|\d{3}\s?\d{4}\s?\d{2}\s?\d{3})$', re.IGNORECASE)

    def get_system_prompt(self) -> str:
        return """You are an expert VAT registration certificate verification specialist for UK businesses. Your role is to verify the authenticity and validity of VAT registration certificates.

You have deep knowledge of:
- UK VAT registration certificate format
- VAT number structure and validation
- HMRC certificate requirements
- Common certificate fraud indicators
- VAT registration types (standard, flat rate, etc.)

When analyzing a VAT certificate, you must verify:
1. VAT number follows correct UK format (GB + 9 or 12 digits)
2. Business name is present and matches expected records
3. Effective date of registration is clear
4. Certificate appears to be from HMRC
5. No signs of tampering or forgery
6. Registration details are internally consistent

Be especially vigilant for:
- Invalid VAT number formats
- Missing HMRC branding/headers
- Inconsistent dates
- Misspellings or formatting errors
- Signs of digital manipulation
- Expired or revoked registrations"""

    def get_validation_prompt(self, extracted_data: dict[str, Any]) -> str:
        return f"""Analyze this VAT registration certificate data for authenticity and compliance:

EXTRACTED VAT CERTIFICATE DATA:
{self._format_data(extracted_data)}

Perform a thorough verification checking:
1. Is the VAT number in valid UK format (GB + 9 or 12 digits)?
2. Is the business name present and properly formatted?
3. Is the effective date of registration clear and reasonable?
4. Does the certificate appear to be genuine HMRC documentation?
5. Are there any inconsistencies or red flags?
6. Is the registration current (not expired or revoked)?

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
    "vat_number_valid_format": true/false,
    "appears_authentic": true/false,
    "recommended_verification": "description of any additional verification steps"
}}"""

    def _format_data(self, data: dict[str, Any]) -> str:
        """Format extracted data for the prompt."""
        lines = []
        for key, value in data.items():
            if value is not None:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No data extracted"

    async def verify(self, extracted_data: dict[str, Any]) -> VerificationResult:
        """Verify a VAT certificate document.

        Args:
            extracted_data: Dictionary containing extracted VAT certificate fields

        Returns:
            VerificationResult with detailed findings
        """
        anomalies = []

        # 1. Check required fields
        anomalies.extend(self.check_required_fields(extracted_data))

        # 2. Verify VAT number format
        vat_anomalies = self._verify_vat_number(extracted_data)
        anomalies.extend(vat_anomalies)

        # 3. Verify effective date
        date_anomalies = self._verify_effective_date(extracted_data)
        anomalies.extend(date_anomalies)

        # 4. Check business name
        name_anomalies = self._verify_business_name(extracted_data)
        anomalies.extend(name_anomalies)

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
        is_valid = not has_high_severity and len(anomalies) <= 1

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

    def _verify_vat_number(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify VAT number format."""
        anomalies = []

        vat_number = data.get("vat_number")
        if vat_number:
            # Normalize the VAT number
            normalized = str(vat_number).upper().replace(" ", "")

            # Check if it matches UK format
            if not self.UK_VAT_PATTERN.match(vat_number.replace(" ", "")):
                # Try without GB prefix
                if normalized.startswith("GB"):
                    digits = normalized[2:]
                else:
                    digits = normalized

                if not (len(digits) == 9 or len(digits) == 12) or not digits.isdigit():
                    anomalies.append(Anomaly(
                        field="vat_number",
                        issue=f"VAT number format is invalid. UK VAT numbers should be 'GB' followed by 9 or 12 digits.",
                        severity=Severity.HIGH,
                        suggestion="Verify the VAT number with HMRC's online VAT number checker.",
                        expected_value="GB followed by 9 or 12 digits (e.g., GB123456789)",
                        actual_value=vat_number,
                    ))

            # Check modulus 97 validation for 9-digit numbers
            if len(normalized.replace("GB", "")) == 9:
                if not self._validate_vat_checksum(normalized.replace("GB", "")):
                    anomalies.append(Anomaly(
                        field="vat_number",
                        issue="VAT number fails checksum validation",
                        severity=Severity.HIGH,
                        suggestion="The VAT number appears to be mathematically invalid. Verify with HMRC.",
                        actual_value=vat_number,
                    ))

        return anomalies

    def _validate_vat_checksum(self, digits: str) -> bool:
        """Validate UK VAT number using modulus 97 algorithm."""
        if len(digits) != 9 or not digits.isdigit():
            return False

        try:
            # UK VAT validation algorithm
            weights = [8, 7, 6, 5, 4, 3, 2]
            total = sum(int(d) * w for d, w in zip(digits[:7], weights))

            # Calculate check digits
            check_value = 97 - (total % 97)
            expected_check = int(digits[7:9])

            # Check if it matches either standard or branch format
            return expected_check == check_value or expected_check == (check_value + 55) % 97
        except (ValueError, IndexError):
            return False

    def _verify_effective_date(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify effective date is reasonable."""
        from datetime import datetime

        anomalies = []
        effective_date = data.get("effective_date")

        if effective_date:
            parsed = self._parse_date(effective_date)
            if parsed:
                # Check if date is in the future
                if parsed > datetime.now():
                    anomalies.append(Anomaly(
                        field="effective_date",
                        issue="Registration effective date is in the future",
                        severity=Severity.HIGH,
                        suggestion="VAT registration effective dates should not be in the future.",
                        actual_value=str(effective_date),
                    ))

                # Check if date is before VAT was introduced (1973 in UK)
                if parsed.year < 1973:
                    anomalies.append(Anomaly(
                        field="effective_date",
                        issue="Registration effective date is before UK VAT system began (1973)",
                        severity=Severity.HIGH,
                        suggestion="The effective date appears to be invalid.",
                        actual_value=str(effective_date),
                    ))

        return anomalies

    def _verify_business_name(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify business name is reasonable."""
        anomalies = []

        business_name = data.get("business_name")
        if business_name:
            name = str(business_name).strip()

            # Check for suspiciously short names
            if len(name) < 2:
                anomalies.append(Anomaly(
                    field="business_name",
                    issue="Business name is suspiciously short",
                    severity=Severity.MEDIUM,
                    suggestion="Verify the full legal business name is shown.",
                    actual_value=name,
                ))

            # Check for common placeholder text
            placeholders = ["test", "xxx", "company name", "your company"]
            if any(ph in name.lower() for ph in placeholders):
                anomalies.append(Anomaly(
                    field="business_name",
                    issue="Business name appears to be placeholder text",
                    severity=Severity.HIGH,
                    suggestion="The business name doesn't appear to be a real company name.",
                    actual_value=name,
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
            return "VAT certificate verification passed. Certificate appears valid."

        high_count = sum(1 for a in anomalies if a.severity == Severity.HIGH)
        medium_count = sum(1 for a in anomalies if a.severity == Severity.MEDIUM)

        if high_count > 0:
            return f"VAT certificate has {high_count} critical issue(s) - verification with HMRC recommended."
        elif medium_count > 0:
            return f"VAT certificate has {medium_count} issue(s) to verify."
        else:
            return f"VAT certificate has {len(anomalies)} minor observation(s)."
