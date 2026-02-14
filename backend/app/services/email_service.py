"""Backward compatibility: Re-export from new location."""

from app.services.email import EmailService, EmailNotificationService

__all__ = ["EmailService", "EmailNotificationService"]
