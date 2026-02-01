"""Backward compatibility: Re-export from new location."""

from app.models.shared import Base, TimestampMixin

__all__ = ["Base", "TimestampMixin"]
