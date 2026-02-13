"""Pydantic schemas for Request Templates."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.requests.template import RequestTemplate, RequestTemplateItem


# Template Schemas
class RequestTemplateItemResponse(BaseModel):
    """Schema for RequestTemplateItem response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    document_type_id: int | None
    description: str | None
    expected_count: int
    is_required: bool
    order_index: int
    created_at: datetime
    updated_at: datetime


class RequestTemplateResponse(BaseModel):
    """Schema for RequestTemplate response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    client_type: str | None
    engagement_type: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: list[RequestTemplateItemResponse] = []


class RequestTemplateList(BaseModel):
    """Schema for listing request templates."""

    items: list[RequestTemplateResponse]
    total: int


# Request schemas for creating request sets from templates
class CreateRequestSetFromTemplate(BaseModel):
    """Schema for creating a RequestSet from a template."""

    engagement_id: int
    template_id: int
    name_override: str | None = None
