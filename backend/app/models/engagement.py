"""Backward compatibility: Re-export from new location."""

from app.models.engagements import Engagement, EngagementType, EngagementStatus

__all__ = ["Engagement", "EngagementType", "EngagementStatus"]
