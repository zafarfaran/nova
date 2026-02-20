"""Backward compatibility: Re-export from new location."""

from app.services.audit import AuditService

__all__ = ["AuditService"]
