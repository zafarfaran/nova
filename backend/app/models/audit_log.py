"""Backward compatibility: Re-export from new location."""

from app.models.audit import AuditLog

__all__ = ["AuditLog"]
