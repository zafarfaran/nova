"""Pydantic schemas for Client."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.clients import EntityType


class ClientBase(BaseModel):
    """Base schema for Client."""

    name: str
    vat_number: str | None = None
    entity_type: EntityType = EntityType.LIMITED_COMPANY
    client_type: str | None = None  # "sole_trader" or "limited_company"
    contact_email: EmailStr | None = None
    contact_name: str | None = None
    address: str | None = None
    notes: str | None = None


class ClientCreate(ClientBase):
    """Schema for creating a Client."""

    pass


class ClientUpdate(BaseModel):
    """Schema for updating a Client."""

    name: str | None = None
    vat_number: str | None = None
    entity_type: EntityType | None = None
    client_type: str | None = None  # "sole_trader" or "limited_company"
    contact_email: EmailStr | None = None
    contact_name: str | None = None
    address: str | None = None
    notes: str | None = None


class ClientResponse(ClientBase):
    """Schema for Client response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ClientList(BaseModel):
    """Schema for listing clients."""

    items: list[ClientResponse]
    total: int


class OnboardingCompleteRequest(BaseModel):
    """Schema for onboarding completion notifications."""

    client_id: int
    completed_items: int | None = None
    not_applicable_items: int | None = None
    total_items: int | None = None
    engagement_id: int | None = None
    vat_period_id: int | None = None  # Deprecated: use engagement_id


class OnboardingCompleteResponse(BaseModel):
    """Response schema for onboarding completion."""

    success: bool
    message: str
    client_id: int
    engagement_id: int | None = None
