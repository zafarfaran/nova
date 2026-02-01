"""Backward compatibility: Re-export from new location."""

from app.schemas.audit.audit import (
    AuditLogResponse,
    AuditLogList,
)

__all__ = [
    "AuditLogResponse",
    "AuditLogList",
]
