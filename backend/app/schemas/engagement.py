"""Backward compatibility: Re-export from new location."""

from app.schemas.engagements import (
    EngagementBase,
    EngagementCreate,
    EngagementUpdate,
    EngagementResponse,
    EngagementList,
)

__all__ = [
    "EngagementBase",
    "EngagementCreate",
    "EngagementUpdate",
    "EngagementResponse",
    "EngagementList",
]
