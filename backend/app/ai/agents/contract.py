"""Contract verification agent."""

from decimal import Decimal, InvalidOperation
from typing import Any

from .base import Anomaly, BaseDocumentAgent, Severity, VerificationResult


class ContractVerificationAgent(BaseDocumentAgent):
    """Specialized agent for verifying contracts.

    This agent checks:
    - Required parties and signatures
    - Contract dates and terms
    - Payment terms and amounts
    - VAT-related clauses
    - Contract completeness
    """

    @property
    def document_type(self) -> str:
        return "CONTRACT"

    @property
    def required_fields(self) -> list[str]:
        return [
            "party_1_name",
            "party_2_name",
            "contract_date",
            "contract_value",
        ]

    def get_system_prompt(self) -> str:
        return """You are an expert contract verification specialist for UK business and VAT compliance. Your role is to analyze contracts for completeness and VAT-relevant information.

You have deep knowledge of:
- UK contract law basics
- VAT treatment of contract payments
- Payment terms and milestones
- Service vs goods classification for VAT
- Common contract issues affecting VAT

When analyzing a contract, you must verify:
1. All parties are clearly identified
2. Contract date and effective dates are clear
3. Contract value/payment terms are specified
4. VAT treatment is addressed (inclusive/exclusive)
5. Payment milestones align with VAT point rules
6. Goods vs services classification is clear
7. Contract appears complete (not missing pages)

Be especially vigilant for:
- Missing party identification
- Unclear payment terms
- No mention of VAT treatment
- Inconsistent dates
- Missing signatures (if applicable)
- Incomplete or draft documents
- Terms that could affect VAT treatment"""

    def get_validation_prompt(self, extracted_data: dict[str, Any]) -> str:
        return f"""Analyze this contract data for completeness and VAT compliance:

EXTRACTED CONTRACT DATA:
{self._format_data(extracted_data)}

Perform a thorough verification checking:
1. Are all parties clearly identified?
2. Is the contract date clear and reasonable?
3. Are payment terms/contract value specified?
4. Is VAT treatment mentioned (prices inclusive/exclusive of VAT)?
5. Are payment milestones clear (affects VAT point)?
6. Is it clear whether this is for goods or services?
7. Does the contract appear complete?

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
    "vat_treatment_specified": true/false,
    "contract_type": "goods|services|mixed|unclear",
    "payment_schedule_clear": true/false
}}"""

    def _format_data(self, data: dict[str, Any]) -> str:
        """Format extracted data for the prompt."""
        lines = []
        for key, value in data.items():
            if value is not None:
                if isinstance(value, list):
                    lines.append(f"- {key}: {', '.join(str(v) for v in value)}")
                else:
                    lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No data extracted"

    async def verify(self, extracted_data: dict[str, Any]) -> VerificationResult:
        """Verify a contract document.

        Args:
            extracted_data: Dictionary containing extracted contract fields

        Returns:
            VerificationResult with detailed findings
        """
        anomalies = []

        # 1. Check required fields
        anomalies.extend(self.check_required_fields(extracted_data))

        # 2. Verify contract dates
        date_anomalies = self._verify_dates(extracted_data)
        anomalies.extend(date_anomalies)

        # 3. Verify contract value
        value_anomalies = self._verify_contract_value(extracted_data)
        anomalies.extend(value_anomalies)

        # 4. Check VAT treatment
        vat_anomalies = self._check_vat_treatment(extracted_data)
        anomalies.extend(vat_anomalies)

        # 5. Check parties
        party_anomalies = self._verify_parties(extracted_data)
        anomalies.extend(party_anomalies)

        # 6. Call AI for deeper analysis
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
        is_valid = not has_high_severity and len(anomalies) <= 3

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

    def _verify_dates(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify contract dates are reasonable."""
        from datetime import datetime, timedelta

        anomalies = []

        contract_date = data.get("contract_date")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if contract_date:
            parsed = self._parse_date(contract_date)
            if parsed:
                # Check if contract date is in the distant future
                if parsed > datetime.now() + timedelta(days=365):
                    anomalies.append(Anomaly(
                        field="contract_date",
                        issue="Contract date is more than a year in the future",
                        severity=Severity.MEDIUM,
                        suggestion="Verify the contract date is correct.",
                        actual_value=str(contract_date),
                    ))

        # Check if end date is before start date
        if start_date and end_date:
            start_parsed = self._parse_date(start_date)
            end_parsed = self._parse_date(end_date)
            if start_parsed and end_parsed and end_parsed < start_parsed:
                anomalies.append(Anomaly(
                    field="contract_dates",
                    issue="Contract end date is before start date",
                    severity=Severity.HIGH,
                    suggestion="Verify the contract period dates.",
                    expected_value=f"End date after {start_date}",
                    actual_value=str(end_date),
                ))

        return anomalies

    def _verify_contract_value(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify contract value is reasonable."""
        anomalies = []

        contract_value = self._to_decimal(data.get("contract_value"))

        if contract_value is not None:
            # Check for zero or negative values
            if contract_value <= 0:
                anomalies.append(Anomaly(
                    field="contract_value",
                    issue="Contract value is zero or negative",
                    severity=Severity.HIGH,
                    suggestion="Verify the contract value. Zero-value contracts may have VAT implications.",
                    actual_value=str(contract_value),
                ))

        return anomalies

    def _check_vat_treatment(self, data: dict[str, Any]) -> list[Anomaly]:
        """Check if VAT treatment is specified."""
        anomalies = []

        vat_inclusive = data.get("vat_inclusive")
        vat_rate = data.get("vat_rate")
        vat_amount = data.get("vat_amount")

        # If no VAT information is provided, flag it
        if vat_inclusive is None and vat_rate is None and vat_amount is None:
            contract_value = self._to_decimal(data.get("contract_value"))
            # Only flag if there's a significant contract value
            if contract_value and contract_value > Decimal("1000"):
                anomalies.append(Anomaly(
                    field="vat_treatment",
                    issue="Contract does not specify VAT treatment (inclusive/exclusive)",
                    severity=Severity.MEDIUM,
                    suggestion="For VAT compliance, contracts should clearly state whether prices include or exclude VAT.",
                ))

        return anomalies

    def _verify_parties(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify contract parties are properly identified."""
        anomalies = []

        party_1 = data.get("party_1_name")
        party_2 = data.get("party_2_name")

        if party_1 and party_2:
            # Check if parties are the same
            if str(party_1).lower().strip() == str(party_2).lower().strip():
                anomalies.append(Anomaly(
                    field="contract_parties",
                    issue="Both contract parties appear to be the same entity",
                    severity=Severity.HIGH,
                    suggestion="A contract typically requires two different parties.",
                    actual_value=f"{party_1} = {party_2}",
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
            return "Contract verification passed. Document appears complete."

        high_count = sum(1 for a in anomalies if a.severity == Severity.HIGH)
        medium_count = sum(1 for a in anomalies if a.severity == Severity.MEDIUM)

        if high_count > 0:
            return f"Contract has {high_count} critical issue(s) requiring attention."
        elif medium_count > 0:
            return f"Contract has {medium_count} issue(s) to review for VAT compliance."
        else:
            return f"Contract has {len(anomalies)} minor observation(s)."
