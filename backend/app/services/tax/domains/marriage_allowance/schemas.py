"""Pydantic schemas for the marriage_allowance domain."""

from pydantic import BaseModel


class MarriageAllowanceRequest(BaseModel):
    transferor_income: float
    recipient_income: float
    transferor_pension_contributions: float = 0
    recipient_pension_contributions: float = 0
    tax_year: str = "2025/26"
