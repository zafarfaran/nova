"""Client domain schemas."""

from app.schemas.clients.client import (
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
