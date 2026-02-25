"""Pydantic schemas for the national_insurance domain."""

from pydantic import BaseModel

from app.services.tax.domains.income_tax.schemas import IncomeSourceInput


class NIRequest(BaseModel):
    income_sources: list[IncomeSourceInput]
    tax_year: str = "2025/26"
