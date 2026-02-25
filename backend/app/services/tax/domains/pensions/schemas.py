"""Pydantic schemas for the pensions domain."""

from pydantic import BaseModel

from app.services.tax.domains.income_tax.schemas import IncomeSourceInput


class PensionAARequest(BaseModel):
    income_sources: list[IncomeSourceInput]
    pension_contributions: float = 0
    employer_contributions: float = 0
    contributions_by_year: dict[str, float] | None = None
    mpaa_triggered: bool = False
    tax_year: str = "2025/26"


class PersonalPensionRequest(BaseModel):
    income_sources: list[IncomeSourceInput]
    proposed_contribution: float
    current_contribution: float = 0
    employer_contributions: float = 0
    gift_aid: float = 0
    region: str = "england"
    number_of_children: int = 0
    claims_child_benefit: bool = False
    contributions_by_year: dict[str, float] | None = None


class SalarySacrificeRequest(BaseModel):
    gross_salary: float
    sacrifice_amount: float
    current_sacrifice: float = 0
    other_income_sources: list[IncomeSourceInput] | None = None
    region: str = "england"
    number_of_children: int = 0
    claims_child_benefit: bool = False
    contributions_by_year: dict[str, float] | None = None
