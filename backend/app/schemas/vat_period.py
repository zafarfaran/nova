"""Pydantic schemas for VAT Period."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.vat_period import PeriodStatus


class VATPeriodBase(BaseModel):
    """Base schema for VAT Period."""

    client_id: int
    period_start: date
    period_end: date
    due_date: date | None = None
    status: PeriodStatus = PeriodStatus.DRAFT
    reference: str | None = None
    notes: str | None = None


class VATPeriodCreate(VATPeriodBase):
    """Schema for creating a VAT Period."""

    pass


class VATPeriodUpdate(BaseModel):
    """Schema for updating a VAT Period."""

    period_start: date | None = None
    period_end: date | None = None
    due_date: date | None = None
    status: PeriodStatus | None = None
    is_locked: bool | None = None
    reference: str | None = None
    notes: str | None = None


class VATPeriodResponse(VATPeriodBase):
    """Schema for VAT Period response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_locked: bool
    created_at: datetime
    updated_at: datetime


class VATPeriodList(BaseModel):
    """Schema for listing VAT periods."""

    items: list[VATPeriodResponse]
    total: int
