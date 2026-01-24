"""Pydantic schemas for Audit Trail."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditTrailEntryResponse(BaseModel):
    """Schema for Audit Trail Entry response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    vat_period_id: int
    action: str
    description: str | None
    performed_by: str | None
    performed_at: datetime
    entity_type: str | None
    entity_id: int | None
    old_value: str | None
    new_value: str | None
    created_at: datetime


class AuditTrailList(BaseModel):
    """Schema for listing audit trail entries."""

    items: list[AuditTrailEntryResponse]
    total: int
