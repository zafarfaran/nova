"""API routes for Email management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.database import get_db
from app.schemas.email import (
    EmailPurpose,
    EmailRequest,
    EmailResponse,
    EmailTone,
)
from app.services.email import EmailService

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/send", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_email(
    request: EmailRequest,
    db: Session = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
) -> EmailResponse:
    """Send an email with optional AI-generated content.

    If subject or body is not provided, they will be generated using AI based on:
    - purpose: The purpose of the email (e.g., reminder, missing_documents)
    - tone: The tone of the email (e.g., professional, friendly)
    - client_id: Optional client ID for context
    - context_data: Additional context for AI generation
    """
    service = EmailService(db=db, ai_provider=ai_provider)

    try:
        response = await service.send_email(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )


@router.post("/preview", response_model=dict, status_code=status.HTTP_200_OK)
async def preview_email(
    purpose: EmailPurpose,
    tone: EmailTone,
    recipient_name: str | None = None,
    client_id: int | None = None,
    context_data: dict | None = None,
    db: Session = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
) -> dict:
    """Generate email preview without sending.

    This endpoint generates email subject and body using AI without actually sending the email.
    Useful for previewing what the AI will generate before sending.
    """
    service = EmailService(db=db, ai_provider=ai_provider)

    try:
        preview = await service.generate_preview(
            purpose=purpose,
            tone=tone,
            recipient_name=recipient_name,
            client_id=client_id,
            context_data=context_data,
        )
        return preview
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate email preview: {str(e)}",
        )
