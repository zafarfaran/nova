"""Pydantic schemas for the income_tax domain."""

from typing import Literal

from pydantic import BaseModel


class IncomeSourceInput(BaseModel):
    type: Literal[
        "employment",
        "self_employment",
        "rental",
        "pension_income",
        "savings",
        "dividends",
        "other",
    ]
    gross_amount: float
    label: str = ""


class IncomeTaxRequest(BaseModel):
    income_sources: list[IncomeSourceInput]
    pension_contributions: float = 0
    gift_aid: float = 0
    region: str = "england"
    tax_year: str = "2025/26"
