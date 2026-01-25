"""Payroll verification agent."""

from decimal import Decimal, InvalidOperation
from typing import Any

from .base import Anomaly, BaseDocumentAgent, Severity, VerificationResult


class PayrollVerificationAgent(BaseDocumentAgent):
    """Specialized agent for verifying payroll documents.

    This agent checks:
    - Required fields (employee details, pay period, gross/net pay)
    - Tax deductions (PAYE, NI)
    - Pension contributions
    - Statutory payments (SSP, SMP, SPP)
    - RTI compliance requirements
    - Payroll calculation accuracy
    """

    @property
    def document_type(self) -> str:
        return "PAYROLL"

    @property
    def required_fields(self) -> list[str]:
        return [
            "employee_name",
            "pay_period",
            "gross_pay",
            "net_pay",
            "paye_tax",
            "national_insurance",
        ]

    def get_system_prompt(self) -> str:
        return """You are an expert payroll verification specialist for UK tax compliance. Your role is to analyze payroll documents and ensure they meet HMRC requirements.

You have deep knowledge of:
- UK PAYE (Pay As You Earn) system
- National Insurance contributions (Class 1)
- Pension auto-enrollment requirements
- Statutory payments (SSP, SMP, SPP, ShPP, SAP)
- RTI (Real Time Information) reporting requirements
- Tax codes and their application
- Student loan deductions
- Apprenticeship levy (for larger employers)

When analyzing payroll, you must verify:
1. Employee identification details
2. Pay period is clearly defined
3. Gross pay breakdown is complete
4. Tax deductions match tax code
5. NI contributions are correct for the earnings band
6. Pension contributions meet minimum requirements (if applicable)
7. Net pay calculation is accurate
8. Year-to-date figures are consistent

Be especially vigilant for:
- Incorrect tax codes applied
- NI calculated on wrong earnings band
- Missing pension contributions for eligible employees
- Statutory payment calculation errors
- Inconsistent year-to-date totals
- Missing or invalid National Insurance numbers
- Payments that don't align with contracted hours/salary"""

    def get_validation_prompt(self, extracted_data: dict[str, Any]) -> str:
        return f"""Analyze this payroll data for anomalies and HMRC compliance:

EXTRACTED PAYROLL DATA:
{self._format_data(extracted_data)}

Perform a thorough verification checking:
1. Are employee details complete (name, NI number)?
2. Is the pay period clearly specified?
3. Is gross pay itemized (basic, overtime, bonuses)?
4. Are tax deductions correct for the apparent tax code?
5. Are NI contributions in the correct band?
6. If pension contributions shown, do they meet minimums?
7. Does net pay = gross pay - all deductions?
8. Are year-to-date figures consistent with this period?
9. Are there any red flags for payroll fraud?

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
    "rti_compliant": true/false,
    "requires_hmrc_correction": true/false,
    "tax_code_valid": true/false
}}"""

    def _format_data(self, data: dict[str, Any]) -> str:
        """Format extracted data for the prompt."""
        lines = []
        for key, value in data.items():
            if value is not None:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No data extracted"

    async def verify(self, extracted_data: dict[str, Any]) -> VerificationResult:
        """Verify a payroll document.

        Args:
            extracted_data: Dictionary containing extracted payroll fields

        Returns:
            VerificationResult with detailed findings
        """
        anomalies = []

        # 1. Check required fields
        anomalies.extend(self.check_required_fields(extracted_data))

        # 2. Verify NI number format
        ni_anomalies = self._verify_ni_number(extracted_data)
        anomalies.extend(ni_anomalies)

        # 3. Verify tax code format
        tax_anomalies = self._verify_tax_code(extracted_data)
        anomalies.extend(tax_anomalies)

        # 4. Verify net pay calculation
        calc_anomalies = self._verify_net_pay_calculation(extracted_data)
        anomalies.extend(calc_anomalies)

        # 5. Verify NI contributions are reasonable
        ni_contrib_anomalies = self._verify_ni_contributions(extracted_data)
        anomalies.extend(ni_contrib_anomalies)

        # 6. Verify pension contributions
        pension_anomalies = self._verify_pension(extracted_data)
        anomalies.extend(pension_anomalies)

        # 7. Call AI for deeper analysis
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

    def _verify_ni_number(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify National Insurance number format."""
        import re
        anomalies = []

        ni_number = data.get("ni_number") or data.get("national_insurance_number")

        if ni_number:
            # UK NI number format: 2 letters, 6 numbers, 1 letter (e.g., AB123456C)
            ni_pattern = r"^[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$"
            cleaned = str(ni_number).upper().replace(" ", "")

            if not re.match(ni_pattern, cleaned):
                anomalies.append(Anomaly(
                    field="ni_number",
                    issue="National Insurance number format appears invalid",
                    severity=Severity.HIGH,
                    suggestion="Verify the NI number is correct. Valid format: AB123456C",
                    actual_value=ni_number,
                ))

        return anomalies

    def _verify_tax_code(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify tax code format and reasonableness."""
        import re
        anomalies = []

        tax_code = data.get("tax_code")

        if tax_code:
            tax_code_str = str(tax_code).upper().strip()

            # Common tax code patterns: 1257L, BR, D0, D1, NT, K codes, S codes (Scotland), C codes (Wales)
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
                anomalies.append(Anomaly(
                    field="tax_code",
                    issue=f"Tax code '{tax_code}' format may be invalid",
                    severity=Severity.MEDIUM,
                    suggestion="Verify the tax code with HMRC or the employee's P45/P60.",
                    actual_value=tax_code,
                ))

            # Check for emergency tax codes that might need attention
            if tax_code_str.endswith("W1") or tax_code_str.endswith("M1") or "X" in tax_code_str:
                anomalies.append(Anomaly(
                    field="tax_code",
                    issue="Emergency/week 1/month 1 tax code detected",
                    severity=Severity.LOW,
                    suggestion="Employee may be on emergency tax. Verify if a proper tax code should have been applied.",
                    actual_value=tax_code,
                ))

        return anomalies

    def _verify_net_pay_calculation(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify net pay = gross pay - deductions."""
        anomalies = []

        gross = self._to_decimal(data.get("gross_pay"))
        net = self._to_decimal(data.get("net_pay"))
        paye = self._to_decimal(data.get("paye_tax") or data.get("income_tax")) or Decimal("0")
        ni = self._to_decimal(data.get("national_insurance") or data.get("ni_employee")) or Decimal("0")
        pension = self._to_decimal(data.get("pension_employee") or data.get("pension_contribution")) or Decimal("0")
        student_loan = self._to_decimal(data.get("student_loan")) or Decimal("0")
        other_deductions = self._to_decimal(data.get("other_deductions")) or Decimal("0")

        if gross is not None and net is not None:
            total_deductions = paye + ni + pension + student_loan + other_deductions
            expected_net = gross - total_deductions

            # Allow small tolerance for rounding
            tolerance = Decimal("0.02")
            if abs(expected_net - net) > tolerance:
                anomalies.append(Anomaly(
                    field="net_pay",
                    issue="Net pay calculation doesn't match deductions",
                    severity=Severity.HIGH,
                    suggestion="Review all deductions. Net pay should equal gross pay minus all deductions.",
                    expected_value=f"£{expected_net:.2f}",
                    actual_value=f"£{net:.2f}",
                ))

        return anomalies

    def _verify_ni_contributions(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify NI contributions are reasonable for the earnings."""
        anomalies = []

        gross = self._to_decimal(data.get("gross_pay"))
        ni = self._to_decimal(data.get("national_insurance") or data.get("ni_employee"))

        if gross is not None and ni is not None:
            # 2024/25 NI rates for Category A:
            # 0% on earnings up to £242/week (£1,048/month)
            # 8% on earnings between £242-£967/week (£1,048-£4,189/month)
            # 2% on earnings above £967/week (£4,189/month)

            # This is a simplified check - assumes monthly pay
            monthly_threshold = Decimal("1048")
            upper_limit = Decimal("4189")

            if gross <= monthly_threshold:
                # Should be 0 NI
                if ni > Decimal("0.50"):  # Small tolerance
                    anomalies.append(Anomaly(
                        field="national_insurance",
                        issue="NI contributions charged on earnings below threshold",
                        severity=Severity.MEDIUM,
                        suggestion=f"Earnings of £{gross:.2f} are below the NI threshold of £{monthly_threshold}",
                        expected_value="£0.00 or minimal",
                        actual_value=f"£{ni:.2f}",
                    ))
            elif ni == Decimal("0") and gross > monthly_threshold:
                anomalies.append(Anomaly(
                    field="national_insurance",
                    issue="No NI contributions on earnings above threshold",
                    severity=Severity.MEDIUM,
                    suggestion="Unless exempt (e.g., over state pension age), NI should be deducted.",
                    expected_value="NI contribution expected",
                    actual_value="£0.00",
                ))

        return anomalies

    def _verify_pension(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify pension contributions if present."""
        anomalies = []

        gross = self._to_decimal(data.get("gross_pay"))
        pension = self._to_decimal(data.get("pension_employee") or data.get("pension_contribution"))

        # Check if there's pension data
        if pension is not None and gross is not None and pension > Decimal("0"):
            # Auto-enrollment minimum is 5% employee contribution (of qualifying earnings)
            # For simplicity, check if it's a reasonable percentage (1% to 40%)
            percentage = (pension / gross) * 100

            if percentage < Decimal("1"):
                anomalies.append(Anomaly(
                    field="pension",
                    issue="Pension contribution seems unusually low",
                    severity=Severity.LOW,
                    suggestion="Minimum auto-enrollment contribution is typically 5% employee + 3% employer.",
                    actual_value=f"{percentage:.1f}%",
                ))
            elif percentage > Decimal("40"):
                anomalies.append(Anomaly(
                    field="pension",
                    issue="Pension contribution seems unusually high",
                    severity=Severity.LOW,
                    suggestion="Verify this is correct. Very high pension contributions may have tax implications.",
                    actual_value=f"{percentage:.1f}%",
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

    def _generate_summary(self, anomalies: list[Anomaly]) -> str:
        """Generate a summary based on anomalies found."""
        if not anomalies:
            return "Payroll verification passed. All calculations and deductions appear correct."

        high_count = sum(1 for a in anomalies if a.severity == Severity.HIGH)
        medium_count = sum(1 for a in anomalies if a.severity == Severity.MEDIUM)

        if high_count > 0:
            return f"Payroll has {high_count} critical issue(s) - requires immediate review for HMRC compliance."
        elif medium_count > 0:
            return f"Payroll has {medium_count} issue(s) to review for accuracy."
        else:
            return f"Payroll has {len(anomalies)} minor observation(s)."
