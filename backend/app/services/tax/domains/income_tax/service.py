"""Income Tax domain module.

Wraps the ANI and income tax engine calculators to provide a
domain-level calculation with observations and API routes.
"""

import logging
from dataclasses import asdict

from fastapi import APIRouter

from app.services.tax.domains.base import BaseTaxDomain
from app.tax.ani import calculate_adjusted_net_income
from app.tax.income_tax import calculate_income_tax
from app.tax.types import IncomeSource, IncomeType, NON_SAVINGS_TYPES

logger = logging.getLogger(__name__)


class IncomeTaxDomain(BaseTaxDomain):
    """Income tax calculation domain."""

    @property
    def name(self) -> str:
        return "income_tax"

    @property
    def display_name(self) -> str:
        return "Income Tax"

    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Calculate income tax from client data.

        Expects client_data with:
            income_sources: list of dicts with type, gross_amount, label
            pension_contributions: float (optional)
            gift_aid: float (optional)
            region: str (optional, default "england")
        """
        # Parse income sources
        raw_sources = client_data.get("income_sources", [])
        income_sources = [
            IncomeSource(
                source_type=IncomeType(s["type"]),
                gross_amount=float(s["gross_amount"]),
                label=s.get("label", ""),
            )
            for s in raw_sources
        ]

        pension_contributions = float(client_data.get("pension_contributions", 0))
        gift_aid = float(client_data.get("gift_aid", 0))
        region = client_data.get("region", "england")
        is_scottish = region.lower() == "scotland"

        # Categorise income
        non_savings = sum(
            s.gross_amount for s in income_sources if s.source_type in NON_SAVINGS_TYPES
        )
        savings = sum(
            s.gross_amount for s in income_sources if s.source_type == IncomeType.SAVINGS
        )
        dividends = sum(
            s.gross_amount for s in income_sources if s.source_type == IncomeType.DIVIDENDS
        )
        total_income = non_savings + savings + dividends

        # Compute ANI
        ani_result = calculate_adjusted_net_income(
            total_income,
            pension_contributions=pension_contributions,
            gift_aid=gift_aid,
            tax_year=tax_year,
        )

        # Compute income tax
        it_result = calculate_income_tax(
            non_savings_income=non_savings,
            savings_income=savings,
            dividend_income=dividends,
            personal_allowance=ani_result.personal_allowance,
            is_scottish=is_scottish,
            gift_aid=gift_aid,
            pension_contributions=pension_contributions,
            tax_year=tax_year,
        )

        # Compute effective rate
        effective_rate = (
            round(it_result.total_income_tax / total_income * 100, 2)
            if total_income > 0
            else 0.0
        )

        # Serialise band results
        non_savings_bands = [asdict(b) for b in it_result.non_savings_bands]
        savings_bands = [asdict(b) for b in it_result.savings_bands]
        dividend_bands = [asdict(b) for b in it_result.dividend_bands]

        logger.info(
            "Income tax domain calculated: total_income=%.2f, tax=%.2f",
            total_income,
            it_result.total_income_tax,
        )

        return {
            "total_income": total_income,
            "adjusted_net_income": ani_result.adjusted_net_income,
            "personal_allowance": ani_result.personal_allowance,
            "pa_status": str(ani_result.pa_status),
            "in_pa_taper_zone": ani_result.in_taper_zone,
            "taxable_income": it_result.taxable_income,
            "total_income_tax": it_result.total_income_tax,
            "non_savings_tax": it_result.non_savings_tax,
            "savings_tax": it_result.savings_tax,
            "dividend_tax": it_result.dividend_tax,
            "effective_rate": effective_rate,
            "personal_savings_allowance": it_result.personal_savings_allowance,
            "dividend_allowance_used": it_result.dividend_allowance_used,
            "non_savings_bands": non_savings_bands,
            "savings_bands": savings_bands,
            "dividend_bands": dividend_bands,
            # Internal keys for downstream domains
            "_ani_result": ani_result,
            "_it_result": it_result,
        }

    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Flag notable income tax observations."""
        observations: list[dict] = []

        if calculation_result.get("in_pa_taper_zone"):
            ani = calculation_result.get("adjusted_net_income", 0)
            observations.append({
                "id": "it_pa_taper",
                "domain": "income_tax",
                "severity": "high",
                "title": "Personal Allowance taper zone",
                "description": (
                    f"ANI of {ani:,.0f} falls in the 100,000-125,140 range, "
                    "creating an effective 60% marginal rate. Consider pension "
                    "contributions to reduce ANI below 100,000."
                ),
            })

        total_income = calculation_result.get("total_income", 0)
        if total_income > 150_000:
            observations.append({
                "id": "it_additional_rate",
                "domain": "income_tax",
                "severity": "info",
                "title": "Additional rate taxpayer",
                "description": (
                    "Income exceeds the additional rate threshold. "
                    "Review tax-efficient extraction strategies."
                ),
            })

        return observations

    def get_router(self) -> APIRouter | None:
        from app.services.tax.domains.income_tax.routes import router
        return router
