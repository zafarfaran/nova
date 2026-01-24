"""UK VAT rules and constants."""

from decimal import Decimal
from typing import Final

# Standard UK VAT rates
VAT_RATE_STANDARD: Final[Decimal] = Decimal("20.0")
VAT_RATE_REDUCED: Final[Decimal] = Decimal("5.0")
VAT_RATE_ZERO: Final[Decimal] = Decimal("0.0")

VALID_VAT_RATES: Final[tuple[Decimal, ...]] = (
    VAT_RATE_STANDARD,
    VAT_RATE_REDUCED,
    VAT_RATE_ZERO,
)

# UK VAT number format (GB followed by 9 or 12 digits)
VAT_NUMBER_PATTERN: Final[str] = r"^GB\d{9}(\d{3})?$"

# Evidence categories that are required for standard VAT returns
STANDARD_EVIDENCE_CATEGORIES: Final[list[str]] = [
    "sales_invoices",
    "purchase_invoices",
    "credit_notes",
    "bank_statements",
]

# Evidence categories for businesses with imports/exports
INTERNATIONAL_EVIDENCE_CATEGORIES: Final[list[str]] = [
    "import_documents",
    "export_documents",
    "vat_certificates",
]

# VAT return due dates (days after period end)
VAT_RETURN_DUE_DAYS: Final[int] = 37  # 1 month + 7 days

# Tolerance for matching calculations (e.g., net + VAT = gross)
CALCULATION_TOLERANCE: Final[Decimal] = Decimal("0.02")

# VAT thresholds (as of 2024)
VAT_REGISTRATION_THRESHOLD: Final[Decimal] = Decimal("90000")
VAT_DEREGISTRATION_THRESHOLD: Final[Decimal] = Decimal("88000")

# Standard evidence requirements by category
DEFAULT_EVIDENCE_REQUIREMENTS: Final[dict[str, dict]] = {
    "sales_invoices": {
        "description": "Sales invoices issued during the period",
        "required": True,
    },
    "purchase_invoices": {
        "description": "Purchase invoices received during the period",
        "required": True,
    },
    "credit_notes": {
        "description": "Credit notes issued or received",
        "required": False,
    },
    "debit_notes": {
        "description": "Debit notes issued or received",
        "required": False,
    },
    "bank_statements": {
        "description": "Bank statements covering the VAT period",
        "required": True,
    },
    "receipts": {
        "description": "Cash receipts and petty cash records",
        "required": False,
    },
    "contracts": {
        "description": "Contracts supporting major transactions",
        "required": False,
    },
    "import_documents": {
        "description": "Import documentation and customs declarations",
        "required": False,
    },
    "export_documents": {
        "description": "Export documentation and proof of export",
        "required": False,
    },
    "vat_certificates": {
        "description": "VAT certificates and exemption documents",
        "required": False,
    },
    "other": {
        "description": "Other supporting documentation",
        "required": False,
    },
}


def is_valid_vat_rate(rate: Decimal) -> bool:
    """Check if a VAT rate is valid for UK VAT."""
    return rate in VALID_VAT_RATES


def validate_vat_calculation(
    net: Decimal, vat: Decimal, gross: Decimal, rate: Decimal
) -> bool:
    """Validate that VAT calculation is correct within tolerance."""
    expected_vat = net * (rate / Decimal("100"))
    expected_gross = net + expected_vat

    vat_diff = abs(vat - expected_vat)
    gross_diff = abs(gross - expected_gross)

    return vat_diff <= CALCULATION_TOLERANCE and gross_diff <= CALCULATION_TOLERANCE
