"""Backward compatibility: Re-export from new location."""

from app.models.audit.log import AuditLog

__all__ = ["AuditLog"]
