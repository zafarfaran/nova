"""Backward compatibility: Re-export from new location."""

from app.schemas.email import (
    EmailPurpose,
    EmailTone,
    EmailRequest,
    AIEmailGenerationRequest,
    EmailResponse,
)

__all__ = [
    "EmailPurpose",
    "EmailTone",
    "EmailRequest",
    "AIEmailGenerationRequest",
    "EmailResponse",
]
