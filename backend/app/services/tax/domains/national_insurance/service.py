"""National Insurance domain module.

Wraps Class 1, Class 2, and Class 4 NI calculators to provide a
domain-level calculation with observations and API routes.
"""

import logging
from dataclasses import asdict

from fastapi import APIRouter

from app.services.tax.domains.base import BaseTaxDomain
from app.tax.national_insurance import (
    calculate_class_1_ni,
    calculate_class_2_ni,
    calculate_class_4_ni,
)
from app.tax.types import IncomeSource, IncomeType

logger = logging.getLogger(__name__)


class NationalInsuranceDomain(BaseTaxDomain):
    """National Insurance calculation domain."""

    @property
    def name(self) -> str:
        return "national_insurance"

    @property
    def display_name(self) -> str:
        return "National Insurance"

    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Calculate NI contributions from client data.

        Expects client_data with:
            income_sources: list of dicts with type, gross_amount, label
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

        # Sum employment and self-employment income
        employment_income = sum(
            s.gross_amount for s in income_sources if s.source_type == IncomeType.EMPLOYMENT
        )
        se_income = sum(
            s.gross_amount for s in income_sources if s.source_type == IncomeType.SELF_EMPLOYMENT
        )

        # Class 1 NI (employment)
        class_1 = None
        class_1_dict = None
        if employment_income > 0:
            class_1 = calculate_class_1_ni(employment_income, tax_year=tax_year)
            class_1_dict = asdict(class_1)

        # Class 2 + Class 4 NI (self-employment)
        class_2 = None
        class_2_dict = None
        class_4 = None
        class_4_dict = None
        if se_income > 0:
            class_2 = calculate_class_2_ni(se_income, tax_year=tax_year)
            class_2_dict = asdict(class_2)
            class_4 = calculate_class_4_ni(se_income, tax_year=tax_year)
            class_4_dict = asdict(class_4)

        # Compute totals
        employment_ni = class_1.total_employee_ni if class_1 else 0.0
        se_ni = (
            (class_2.annual_ni if class_2 else 0.0)
            + (class_4.total_ni if class_4 else 0.0)
        )
        total_ni = employment_ni + se_ni

        logger.info(
            "NI domain calculated: employment_ni=%.2f, se_ni=%.2f, total=%.2f",
            employment_ni,
            se_ni,
            total_ni,
        )

        return {
            "total_ni": total_ni,
            "employment_ni": employment_ni,
            "self_employment_ni": se_ni,
            "class_1": class_1_dict,
            "class_2": class_2_dict,
            "class_4": class_4_dict,
        }

    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Flag notable NI observations."""
        observations: list[dict] = []

        class_1 = calculation_result.get("class_1")
        if class_1:
            earnings = class_1.get("earnings", 0)
            uel = class_1.get("upper_earnings_limit", 0)
            # Flag when near UEL threshold (within 5,000)
            if 0 < uel - earnings <= 5_000:
                observations.append({
                    "id": "ni_near_uel",
                    "domain": "national_insurance",
                    "severity": "info",
                    "title": "Near Upper Earnings Limit",
                    "description": (
                        f"Employment earnings of {earnings:,.0f} are within "
                        f"5,000 of the Upper Earnings Limit ({uel:,.0f}). "
                        "NI rate drops from the main rate to 2% above this level."
                    ),
                })

        class_4 = calculation_result.get("class_4")
        if class_4:
            profits = class_4.get("profits", 0)
            upl = class_4.get("upper_profit_limit", 0)
            if 0 < upl - profits <= 5_000:
                observations.append({
                    "id": "ni_near_upl",
                    "domain": "national_insurance",
                    "severity": "info",
                    "title": "Near Upper Profits Limit",
                    "description": (
                        f"Self-employment profits of {profits:,.0f} are within "
                        f"5,000 of the Upper Profits Limit ({upl:,.0f}). "
                        "Class 4 NI rate drops above this level."
                    ),
                })

        return observations

    def get_router(self) -> APIRouter | None:
        from app.services.tax.domains.national_insurance.routes import router
        return router
