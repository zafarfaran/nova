"""Pydantic schemas for the capital_gains domain."""

from pydantic import BaseModel


class CapitalGainsRequest(BaseModel):
    gains: float = 0
    losses: float = 0
    tax_year: str = "2025/26"
