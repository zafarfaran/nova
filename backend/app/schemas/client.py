"""Pydantic schemas for Client."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.client import EntityType


class ClientBase(BaseModel):
    """Base schema for Client."""

    name: str
    vat_number: str | None = None
    entity_type: EntityType = EntityType.LIMITED_COMPANY
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
