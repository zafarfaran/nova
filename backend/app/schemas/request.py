"""Pydantic schemas for Request Sets and Items."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.request_set import RequestSetStatus
from app.models.request_item import RequestItemStatus


# Request Set Schemas
class RequestSetBase(BaseModel):
    """Base schema for Request Set."""

    name: str
    status: RequestSetStatus = RequestSetStatus.DRAFT
    due_date: date | None = None


class RequestSetCreate(RequestSetBase):
    """Schema for creating a Request Set."""

    engagement_id: int


class RequestSetUpdate(BaseModel):
    """Schema for updating a Request Set."""

    name: str | None = None
    status: RequestSetStatus | None = None
    due_date: date | None = None


class RequestSetResponse(RequestSetBase):
    """Schema for Request Set response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    engagement_id: int
    created_at: datetime
    updated_at: datetime


class RequestSetList(BaseModel):
    """Schema for listing request sets."""

    items: list[RequestSetResponse]
    total: int


# Request Item Schemas
class RequestItemBase(BaseModel):
    """Base schema for Request Item."""

    description: str | None = None
    expected_count: int = 1
    is_required: bool = True
    status: RequestItemStatus = RequestItemStatus.PENDING
    due_date: date | None = None


class RequestItemCreate(RequestItemBase):
    """Schema for creating a Request Item."""

    request_set_id: int
    document_type_id: int | None = None
    assigned_to_contact_id: int | None = None


class RequestItemUpdate(BaseModel):
    """Schema for updating a Request Item."""

    description: str | None = None
    expected_count: int | None = None
    is_required: bool | None = None
    status: RequestItemStatus | None = None
    due_date: date | None = None
    assigned_to_contact_id: int | None = None


class RequestItemResponse(RequestItemBase):
    """Schema for Request Item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    request_set_id: int
    document_type_id: int | None
    assigned_to_contact_id: int | None
    created_at: datetime
    updated_at: datetime


class RequestItemList(BaseModel):
    """Schema for listing request items."""

    items: list[RequestItemResponse]
    total: int
