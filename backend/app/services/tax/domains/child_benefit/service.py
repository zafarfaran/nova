"""Child Benefit / HICBC domain module.

Wraps the HICBC calculator to provide a domain-level calculation
with observations and API routes.
"""

import logging

from fastapi import APIRouter

from app.services.tax.domains.base import BaseTaxDomain
from app.tax.hicbc import calculate_hicbc

logger = logging.getLogger(__name__)


class ChildBenefitDomain(BaseTaxDomain):
    """Child Benefit and HICBC calculation domain."""

    @property
    def name(self) -> str:
        return "child_benefit"

    @property
    def display_name(self) -> str:
        return "Child Benefit"

    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Calculate HICBC from client data.

        Expects client_data with:
            adjusted_net_income: float
            number_of_children: int (default 1)
            claims_child_benefit: bool (default True)
        """
        adjusted_net_income = float(client_data.get("adjusted_net_income", 0))
        number_of_children = int(client_data.get("number_of_children", 1))
        claims_child_benefit = bool(client_data.get("claims_child_benefit", True))

        if not claims_child_benefit or number_of_children <= 0:
            return {
                "applies": False,
                "child_benefit_annual": 0.0,
                "clawback_percentage": 0.0,
                "hicbc_charge": 0.0,
                "net_benefit": 0.0,
            }

        hicbc_result = calculate_hicbc(
            adjusted_net_income,
            number_of_children=number_of_children,
            tax_year=tax_year,
        )

        logger.info(
            "Child benefit domain calculated: applies=%s, charge=%.2f",
            hicbc_result.applies,
            hicbc_result.hicbc_charge,
        )

        return {
            "applies": hicbc_result.applies,
            "child_benefit_annual": hicbc_result.child_benefit_annual,
            "clawback_percentage": hicbc_result.clawback_percentage,
            "hicbc_charge": hicbc_result.hicbc_charge,
            "net_benefit": hicbc_result.net_benefit,
        }

    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Flag notable child benefit observations."""
        observations: list[dict] = []

        if calculation_result.get("applies"):
            charge = calculation_result.get("hicbc_charge", 0)
            net = calculation_result.get("net_benefit", 0)
            clawback = calculation_result.get("clawback_percentage", 0)

            if clawback >= 100:
                observations.append({
                    "id": "cb_full_clawback",
                    "domain": "child_benefit",
                    "severity": "high",
                    "title": "Full HICBC clawback",
                    "description": (
                        f"HICBC claws back 100% of child benefit ({charge:,.0f}). "
                        "Consider whether it is worth continuing to claim. "
                        "Note: claiming preserves NI credits and the child's NI number."
                    ),
                })
            else:
                observations.append({
                    "id": "cb_partial_clawback",
                    "domain": "child_benefit",
                    "severity": "medium",
                    "title": "Partial HICBC clawback",
                    "description": (
                        f"HICBC claws back {clawback:.0f}% of child benefit "
                        f"(charge: {charge:,.0f}, net benefit: {net:,.0f}). "
                        "Pension contributions could reduce ANI below the "
                        "60,000 threshold to eliminate the charge."
                    ),
                })

        return observations

    def get_router(self) -> APIRouter | None:
        from app.services.tax.domains.child_benefit.routes import router
        return router
