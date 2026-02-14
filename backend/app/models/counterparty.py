"""Backward compatibility: Re-export from new location."""

from app.models.clients import Counterparty, CounterpartyType

__all__ = ["Counterparty", "CounterpartyType"]
