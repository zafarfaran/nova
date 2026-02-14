"""Backward compatibility: Re-export from new location."""

from app.models.clients import FinancialAccount, AccountType

__all__ = ["FinancialAccount", "AccountType"]
