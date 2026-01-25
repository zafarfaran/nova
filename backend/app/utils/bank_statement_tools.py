"""Deterministic tools for bank statement reconciliation."""

from decimal import Decimal, InvalidOperation
from typing import Any


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            cleaned = value.replace(",", "").replace("£", "").replace("$", "").strip()
            return Decimal(cleaned)
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def reconcile_balances(
    opening_balance: Any,
    closing_balance: Any,
    total_credits: Any,
    total_debits: Any,
    tolerance: Decimal = Decimal("0.01"),
) -> dict[str, Any]:
    """Reconcile opening + credits - debits against closing.

    Returns:
        {
            "ok": bool | None,  # None when reconciliation cannot be performed
            "reason": str | None,
            "expected_closing": Decimal | None,
            "difference": Decimal | None,
            "opening": Decimal | None,
            "closing": Decimal | None,
            "credits": Decimal | None,
            "debits": Decimal | None,
        }
    """
    opening = _to_decimal(opening_balance)
    closing = _to_decimal(closing_balance)
    credits = _to_decimal(total_credits)
    debits = _to_decimal(total_debits)

    if opening is None or closing is None:
        return {
            "ok": None,
            "reason": "missing_balances",
            "expected_closing": None,
            "difference": None,
            "opening": opening,
            "closing": closing,
            "credits": credits,
            "debits": debits,
        }

    if credits is None or debits is None:
        return {
            "ok": None,
            "reason": "missing_totals",
            "expected_closing": None,
            "difference": None,
            "opening": opening,
            "closing": closing,
            "credits": credits,
            "debits": debits,
        }

    expected = opening + credits - debits
    difference = abs(expected - closing)

    return {
        "ok": difference <= tolerance,
        "reason": None,
        "expected_closing": expected,
        "difference": difference,
        "opening": opening,
        "closing": closing,
        "credits": credits,
        "debits": debits,
    }
