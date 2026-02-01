"""Email domain schemas."""

from app.schemas.email.email import (
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
