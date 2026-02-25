"""Pydantic schemas for the child_benefit domain."""

from pydantic import BaseModel


class ChildBenefitRequest(BaseModel):
    adjusted_net_income: float
    number_of_children: int = 1
    claims_child_benefit: bool = True
    tax_year: str = "2025/26"
