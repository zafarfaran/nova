"""Pensions domain module.

The most complex domain -- wraps pension annual allowance, personal
pension analysis, and salary sacrifice analysis. Provides three
route endpoints for AA position, personal pension modelling, and
salary sacrifice modelling.
"""

import logging
from dataclasses import asdict

from fastapi import APIRouter

from app.services.tax.domains.base import BaseTaxDomain
from app.tax.ani import calculate_adjusted_net_income
from app.tax.pension_aa import calculate_pension_aa
from app.tax.personal_pension import analyse_personal_pension
from app.tax.salary_sacrifice import analyse_salary_sacrifice
from app.tax.types import IncomeSource, IncomeType, NON_SAVINGS_TYPES

logger = logging.getLogger(__name__)


def _parse_income_sources(raw_sources: list[dict]) -> list[IncomeSource]:
    """Convert raw dicts to IncomeSource objects."""
    return [
        IncomeSource(
            source_type=IncomeType(s["type"]),
            gross_amount=float(s["gross_amount"]),
            label=s.get("label", ""),
        )
        for s in raw_sources
    ]


class PensionsDomain(BaseTaxDomain):
    """Pensions calculation domain."""

    @property
    def name(self) -> str:
        return "pensions"

    @property
    def display_name(self) -> str:
        return "Pensions"

    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Calculate pension annual allowance position from client data.

        Expects client_data with:
            income_sources: list of dicts with type, gross_amount, label
            pension_contributions: float (personal contributions)
            employer_contributions: float
            contributions_by_year: dict[str, float] | None
            mpaa_triggered: bool
        """
        # Parse income sources
        raw_sources = client_data.get("income_sources", [])
        income_sources = _parse_income_sources(raw_sources)

        pension_contributions = float(client_data.get("pension_contributions", 0))
        employer_contributions = float(client_data.get("employer_contributions", 0))
        contributions_by_year = client_data.get("contributions_by_year")
        mpaa_triggered = bool(client_data.get("mpaa_triggered", False))

        # Compute total income
        total_income = sum(s.gross_amount for s in income_sources)

        # Compute ANI (needed for taper check)
        ani_result = calculate_adjusted_net_income(
            total_income,
            pension_contributions=pension_contributions,
            tax_year=tax_year,
        )

        # For the taper test:
        #   threshold_income = total_income - personal_contributions
        #   adjusted_income  = total_income + employer_contributions
        total_pension = pension_contributions + employer_contributions

        aa_result = calculate_pension_aa(
            adjusted_income=total_income + employer_contributions,
            threshold_income=total_income - pension_contributions,
            current_year_contributions=total_pension,
            contributions_by_year=contributions_by_year,
            mpaa_triggered=mpaa_triggered,
            tax_year=tax_year,
        )

        # Serialise carry forward
        carry_forward = [
            {
                "tax_year": cf.tax_year,
                "annual_allowance": cf.annual_allowance,
                "contributions": cf.contributions,
                "unused": cf.unused,
            }
            for cf in aa_result.carry_forward
        ]

        logger.info(
            "Pensions domain calculated: aa=%.0f, tapered=%s, remaining=%.0f",
            aa_result.annual_allowance,
            aa_result.is_tapered,
            aa_result.remaining,
        )

        return {
            "annual_allowance": aa_result.annual_allowance,
            "is_tapered": aa_result.is_tapered,
            "carry_forward": carry_forward,
            "total_available": aa_result.total_available,
            "remaining": aa_result.remaining,
            "current_year_contributions": aa_result.current_year_contributions,
            "mpaa_applies": aa_result.mpaa_applies,
        }

    def model_personal_pension(
        self,
        income_sources: list[IncomeSource],
        proposed_contribution: float,
        *,
        current_contribution: float = 0,
        employer_contributions: float = 0,
        gift_aid: float = 0,
        region: str = "england",
        number_of_children: int = 0,
        claims_child_benefit: bool = False,
        contributions_by_year: dict[str, float] | None = None,
    ) -> dict:
        """Model personal pension contribution scenario."""
        analysis, _tax_position = analyse_personal_pension(
            income_sources=income_sources,
            proposed_contribution=proposed_contribution,
            current_contribution=current_contribution,
            employer_contributions=employer_contributions,
            gift_aid=gift_aid,
            region=region,
            number_of_children=number_of_children,
            claims_child_benefit=claims_child_benefit,
            pension_contributions_by_year=contributions_by_year,
        )
        return analysis

    def model_salary_sacrifice(
        self,
        gross_salary: float,
        sacrifice_amount: float,
        *,
        current_sacrifice: float = 0,
        other_income_sources: list[IncomeSource] | None = None,
        region: str = "england",
        number_of_children: int = 0,
        claims_child_benefit: bool = False,
        contributions_by_year: dict[str, float] | None = None,
    ) -> dict:
        """Model salary sacrifice scenario."""
        analysis, _tax_position = analyse_salary_sacrifice(
            gross_salary=gross_salary,
            sacrifice_amount=sacrifice_amount,
            current_sacrifice=current_sacrifice,
            other_income_sources=other_income_sources,
            region=region,
            number_of_children=number_of_children,
            claims_child_benefit=claims_child_benefit,
            pension_contributions_by_year=contributions_by_year,
        )
        return analysis

    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Flag notable pension observations."""
        observations: list[dict] = []

        if calculation_result.get("is_tapered"):
            aa = calculation_result.get("annual_allowance", 0)
            observations.append({
                "id": "pension_tapered_aa",
                "domain": "pensions",
                "severity": "high",
                "title": "Tapered Annual Allowance",
                "description": (
                    f"Annual allowance has been tapered to {aa:,.0f} due to "
                    "high adjusted income. Review contribution levels to "
                    "avoid an annual allowance charge."
                ),
            })

        remaining = calculation_result.get("remaining", 0)
        if remaining < 0:
            observations.append({
                "id": "pension_aa_exceeded",
                "domain": "pensions",
                "severity": "high",
                "title": "Annual Allowance exceeded",
                "description": (
                    f"Contributions exceed available allowance by "
                    f"{abs(remaining):,.0f}. An annual allowance charge "
                    "will apply on the excess."
                ),
            })
        elif 0 < remaining <= 5_000:
            observations.append({
                "id": "pension_low_headroom",
                "domain": "pensions",
                "severity": "medium",
                "title": "Low pension headroom",
                "description": (
                    f"Only {remaining:,.0f} of pension annual allowance "
                    "remaining. Consider contribution levels carefully."
                ),
            })

        if calculation_result.get("mpaa_applies"):
            observations.append({
                "id": "pension_mpaa",
                "domain": "pensions",
                "severity": "high",
                "title": "Money Purchase Annual Allowance applies",
                "description": (
                    "MPAA has been triggered. Money purchase contributions "
                    "are limited to 10,000 per year with no carry forward."
                ),
            })

        return observations

    def get_router(self) -> APIRouter | None:
        from app.services.tax.domains.pensions.routes import router
        return router
