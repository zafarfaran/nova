"""Pydantic schemas for Audit Log."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Schema for Audit Log response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int | None
    engagement_id: int | None
    entity_type: str | None
    entity_id: int | None
    action: str
    actor_contact_id: int | None
    changes: dict[str, Any]
    created_at: datetime


class AuditLogList(BaseModel):
    """Schema for listing audit log entries."""

    items: list[AuditLogResponse]
    total: int
