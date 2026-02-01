"""Pydantic schemas for Engagement."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.engagement import EngagementStatus, EngagementType


class EngagementBase(BaseModel):
    """Base schema for Engagement."""

    engagement_type: EngagementType = EngagementType.VAT_RETURN
    period_start: date
    period_end: date
    status: EngagementStatus = EngagementStatus.DRAFT
    reference: str | None = None
    due_date: date | None = None
    notes: str | None = None


class EngagementCreate(EngagementBase):
    """Schema for creating an Engagement."""

    client_id: int


class EngagementUpdate(BaseModel):
    """Schema for updating an Engagement."""

    engagement_type: EngagementType | None = None
    period_start: date | None = None
    period_end: date | None = None
    status: EngagementStatus | None = None
    reference: str | None = None
    due_date: date | None = None
    notes: str | None = None
    is_locked: bool | None = None


class EngagementResponse(EngagementBase):
    """Schema for Engagement response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    is_locked: bool
    created_at: datetime
    updated_at: datetime


class EngagementList(BaseModel):
    """Schema for listing engagements."""

    items: list[EngagementResponse]
    total: int
