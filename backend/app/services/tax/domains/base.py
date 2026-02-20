"""Base class for all tax domain modules."""

from abc import ABC, abstractmethod

from fastapi import APIRouter


class BaseTaxDomain(ABC):
    """Every tax domain must implement this interface.

    To add a new domain:
    1. Create a folder under domains/ (e.g. domains/capital_gains/)
    2. Create service.py with a class that extends BaseTaxDomain
    3. Implement calculate(), get_observations(), get_router()
    4. The registry auto-discovers it — no other files need changing.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Machine name, e.g. 'income_tax'. Used as URL slug (hyphens auto-added)."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human name, e.g. 'Income Tax'. Used in UI/reports."""

    @abstractmethod
    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Run this domain's calculation. Returns domain-specific result dict."""

    @abstractmethod
    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Extract planning observations from this domain's calculation result."""

    def get_router(self) -> APIRouter | None:
        """Return this domain's API router, or None if no custom endpoints."""
        return None
