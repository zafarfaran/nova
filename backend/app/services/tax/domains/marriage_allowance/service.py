"""Marriage Allowance domain module.

Wraps the marriage allowance calculator (Phase 3 stub). Catches
NotImplementedError and returns a placeholder result until the
engine module is fully implemented.
"""

import logging

from app.services.tax.domains.base import BaseTaxDomain
from app.tax.ani import calculate_adjusted_net_income
from app.tax.marriage_allowance import calculate_marriage_allowance

logger = logging.getLogger(__name__)


class MarriageAllowanceDomain(BaseTaxDomain):
    """Marriage Allowance calculation domain."""

    @property
    def name(self) -> str:
        return "marriage_allowance"

    @property
    def display_name(self) -> str:
        return "Marriage Allowance"

    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Calculate marriage allowance eligibility and benefit.

        Expects client_data with:
            transferor_income: float
            recipient_income: float
            transferor_pension_contributions: float (optional)
            recipient_pension_contributions: float (optional)
        """
        transferor_income = float(client_data.get("transferor_income", 0))
        recipient_income = float(client_data.get("recipient_income", 0))
        transferor_pension = float(client_data.get("transferor_pension_contributions", 0))
        recipient_pension = float(client_data.get("recipient_pension_contributions", 0))

        # Compute ANI for both parties
        transferor_ani = calculate_adjusted_net_income(
            transferor_income,
            pension_contributions=transferor_pension,
            tax_year=tax_year,
        )
        recipient_ani = calculate_adjusted_net_income(
            recipient_income,
            pension_contributions=recipient_pension,
            tax_year=tax_year,
        )

        try:
            result = calculate_marriage_allowance(transferor_ani, recipient_ani)
            return result
        except NotImplementedError:
            logger.info("Marriage allowance engine not yet implemented (Phase 3)")
            return {
                "status": "placeholder",
                "message": "Marriage allowance calculation not yet implemented (Phase 3)",
                "transferor_ani": transferor_ani.adjusted_net_income,
                "recipient_ani": recipient_ani.adjusted_net_income,
            }

    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Return empty observations (stub domain)."""
        return []
