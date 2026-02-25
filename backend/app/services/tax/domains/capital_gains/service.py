"""Capital Gains Tax domain module.

Placeholder domain -- no engine module exists yet. Returns stub
results with CGT annual exempt amount information.
"""

import logging

from app.services.tax.domains.base import BaseTaxDomain

logger = logging.getLogger(__name__)


class CapitalGainsDomain(BaseTaxDomain):
    """Capital Gains Tax placeholder domain."""

    @property
    def name(self) -> str:
        return "capital_gains"

    @property
    def display_name(self) -> str:
        return "Capital Gains Tax"

    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Return placeholder CGT information.

        Expects client_data with:
            gains: float (optional)
            losses: float (optional)
        """
        logger.info("Capital gains domain: returning placeholder result")
        return {
            "cgt_annual_exempt_amount": 3000,
            "status": "placeholder",
            "message": "CGT module not yet implemented",
        }

    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Return empty observations (placeholder domain)."""
        return []
