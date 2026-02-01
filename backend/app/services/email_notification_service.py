"""Backward compatibility: Re-export from new location."""

from app.services.email import EmailNotificationService

__all__ = ["EmailNotificationService"]
