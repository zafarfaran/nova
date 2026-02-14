"""Backward compatibility: Re-export from new location."""

from app.schemas.clients import (
    ClientBase,
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientList,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
)

__all__ = [
    "ClientBase",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ClientList",
    "OnboardingCompleteRequest",
    "OnboardingCompleteResponse",
]
