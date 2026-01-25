"""Bank statement verification agent."""

from decimal import Decimal, InvalidOperation
from typing import Any

from .base import Anomaly, BaseDocumentAgent, Severity, VerificationResult
from app.utils.bank_statement_tools import reconcile_balances


class BankStatementVerificationAgent(BaseDocumentAgent):
    """Specialized agent for verifying bank statements.

    This agent checks:
    - Required fields (account details, period, balances)
    - Opening and closing balance consistency
    - Transaction totals accuracy
    - Date range coverage
    - Account holder information
    - Unusual transaction patterns
    """

    @property
    def document_type(self) -> str:
        return "BANK_STATEMENT"

    @property
    def required_fields(self) -> list[str]:
        return [
            "account_holder_name",
            "account_number",
            "statement_period_start",
            "statement_period_end",
            "opening_balance",
            "closing_balance",
        ]

    def get_system_prompt(self) -> str:
        return """You are an expert bank statement verification specialist for UK VAT compliance. Your role is to analyze bank statements for accuracy and completeness.

You have deep knowledge of:
- UK banking formats and standards
- Bank statement reconciliation
- Transaction categorization
- Identifying unusual or suspicious patterns
- VAT-relevant transaction identification

When analyzing a bank statement, you must verify:
1. Account holder details are complete and consistent
2. Statement period is clearly defined
3. Opening balance matches previous closing (if available)
4. Transactions sum correctly: Opening + Credits - Debits = Closing
5. All transactions have dates within the statement period
6. No obvious gaps in transaction sequences
7. Transaction descriptions are present and meaningful

Be especially vigilant for:
- Balance discrepancies
- Missing transaction dates
- Transactions outside the statement period
- Round-number-only transactions (potential red flag)
- Unusual patterns in credits/debits
- Missing or redacted information"""

    def get_validation_prompt(self, extracted_data: dict[str, Any]) -> str:
        return f"""Analyze this bank statement data for anomalies and compliance issues:

EXTRACTED BANK STATEMENT DATA:
{self._format_data(extracted_data)}

Perform a thorough verification checking:
1. Are account holder details complete?
2. Is the statement period clearly defined?
3. Do the balances reconcile? (Opening + Credits - Debits = Closing)
4. Are all transactions within the statement period?
5. Are there any gaps or missing information?
6. Are there unusual transaction patterns?
7. Is this statement suitable for VAT reconciliation?

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
    "balance_verified": true/false,
    "period_coverage": "full|partial|unclear",
    "vat_relevant_transactions": number
}}"""

    def _format_data(self, data: dict[str, Any]) -> str:
        """Format extracted data for the prompt."""
        lines = []
        for key, value in data.items():
            if value is not None:
                if key == "transactions" and isinstance(value, list):
                    lines.append(f"- {key}: {len(value)} transactions")
                    # Show first few transactions as sample
                    for i, txn in enumerate(value[:5]):
                        lines.append(f"    [{i+1}] {txn}")
                    if len(value) > 5:
                        lines.append(f"    ... and {len(value) - 5} more")
                else:
                    lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No data extracted"

    async def verify(self, extracted_data: dict[str, Any]) -> VerificationResult:
        """Verify a bank statement document.

        Args:
            extracted_data: Dictionary containing extracted bank statement fields

        Returns:
            VerificationResult with detailed findings
        """
        anomalies = []

        # 1. Check required fields
        anomalies.extend(self.check_required_fields(extracted_data))

        # 2. Verify balance reconciliation
        balance_anomalies = self._verify_balance_reconciliation(extracted_data)
        anomalies.extend(balance_anomalies)

        # 3. Verify statement period
        period_anomalies = self._verify_statement_period(extracted_data)
        anomalies.extend(period_anomalies)

        # 4. Verify account number format
        account_anomalies = self._verify_account_number(extracted_data)
        anomalies.extend(account_anomalies)

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

    def _verify_balance_reconciliation(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify that opening balance + transactions = closing balance."""
        anomalies = []

        try:
            result = reconcile_balances(
                opening_balance=data.get("opening_balance"),
                closing_balance=data.get("closing_balance"),
                total_credits=data.get("total_credits"),
                total_debits=data.get("total_debits"),
            )
            if result["ok"] is False:
                anomalies.append(Anomaly(
                    field="closing_balance",
                    issue=(
                        "Balance reconciliation failed: Opening "
                        f"({result['opening']}) + Credits ({result['credits']}) - "
                        f"Debits ({result['debits']}) = {result['expected_closing']}, "
                        f"but Closing shows {result['closing']}"
                    ),
                    severity=Severity.HIGH,
                    suggestion="The statement balances don't reconcile. This may indicate missing transactions or calculation errors.",
                    expected_value=str(result["expected_closing"]),
                    actual_value=str(result["closing"]),
                ))

            # Check for negative closing balance (unusual for most business accounts)
            closing = result.get("closing")
            if closing is not None and closing < 0:
                anomalies.append(Anomaly(
                    field="closing_balance",
                    issue="Closing balance is negative (overdrawn)",
                    severity=Severity.LOW,
                    suggestion="Verify if overdraft is expected. May affect VAT period cash accounting.",
                    actual_value=str(closing),
                ))

        except (InvalidOperation, TypeError, ValueError):
            pass

        return anomalies

    def _verify_statement_period(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify statement period is valid and reasonable."""
        from datetime import datetime, timedelta

        anomalies = []

        start_date = data.get("statement_period_start")
        end_date = data.get("statement_period_end")

        if start_date and end_date:
            try:
                start = self._parse_date(start_date)
                end = self._parse_date(end_date)

                if start and end:
                    # Check if end is before start
                    if end < start:
                        anomalies.append(Anomaly(
                            field="statement_period",
                            issue="Statement end date is before start date",
                            severity=Severity.HIGH,
                            suggestion="Verify the statement period dates are correct.",
                            expected_value=f"End date after {start_date}",
                            actual_value=end_date,
                        ))

                    # Check if period is unusually long (more than 3 months)
                    if (end - start).days > 93:
                        anomalies.append(Anomaly(
                            field="statement_period",
                            issue=f"Statement covers an unusually long period ({(end - start).days} days)",
                            severity=Severity.LOW,
                            suggestion="Most bank statements are monthly. Verify this covers the correct VAT period.",
                        ))

                    # Check if period is in the future
                    if end > datetime.now():
                        anomalies.append(Anomaly(
                            field="statement_period_end",
                            issue="Statement period extends into the future",
                            severity=Severity.HIGH,
                            suggestion="Statement end date cannot be in the future.",
                            actual_value=end_date,
                        ))

            except Exception:
                pass

        return anomalies

    def _verify_account_number(self, data: dict[str, Any]) -> list[Anomaly]:
        """Verify account number format (UK format: 8 digits)."""
        anomalies = []

        account_number = data.get("account_number")
        if account_number:
            # Remove spaces and dashes
            cleaned = str(account_number).replace(" ", "").replace("-", "")

            # UK account numbers are typically 8 digits
            if not cleaned.isdigit():
                anomalies.append(Anomaly(
                    field="account_number",
                    issue="Account number contains non-numeric characters",
                    severity=Severity.MEDIUM,
                    suggestion="Verify the account number is correct.",
                    actual_value=account_number,
                ))
            elif len(cleaned) != 8:
                anomalies.append(Anomaly(
                    field="account_number",
                    issue=f"Account number length ({len(cleaned)}) doesn't match standard UK format (8 digits)",
                    severity=Severity.LOW,
                    suggestion="UK bank account numbers are typically 8 digits. Verify if this is correct.",
                    actual_value=account_number,
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
            return "Bank statement verification passed. Balances reconcile correctly."

        high_count = sum(1 for a in anomalies if a.severity == Severity.HIGH)
        medium_count = sum(1 for a in anomalies if a.severity == Severity.MEDIUM)

        if high_count > 0:
            return f"Bank statement has {high_count} critical issue(s) - balances may not reconcile."
        elif medium_count > 0:
            return f"Bank statement has {medium_count} issue(s) requiring review."
        else:
            return f"Bank statement has {len(anomalies)} minor observation(s)."
