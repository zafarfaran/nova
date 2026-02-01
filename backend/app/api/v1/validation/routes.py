"""API routes for document validation."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.validation import ValidationStatus
from app.schemas.validation import (
    ValidationResultList,
    ValidationResultResponse,
    ValidationRunResponse,
    ValidationSummary,
)
from app.services.documents import DocumentService
from app.services.engagements import EngagementService
from app.services.validation import ValidationService

router = APIRouter(prefix="/validation", tags=["validation"])


class DocumentRejectionRequest(BaseModel):
    """Request body for document rejection."""
    rejected_by: str
    rejection_reason: str


@router.post("/run/{doc_id}", response_model=ValidationRunResponse)
def run_validation(doc_id: int, db: Session = Depends(get_db)) -> ValidationRunResponse:
    """Run validation on a single document."""
    doc_service = DocumentService(db)
    if not doc_service.get(doc_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    service = ValidationService(db)
    results = service.validate_document(doc_id)

    passed = sum(1 for r in results if r.status == ValidationStatus.PASSED)
    failed = sum(1 for r in results if r.status == ValidationStatus.FAILED)
    warnings = sum(1 for r in results if r.status == ValidationStatus.WARNING)
    skipped = sum(1 for r in results if r.status == ValidationStatus.SKIPPED)

    return ValidationRunResponse(
        document_id=doc_id,
        results=[ValidationResultResponse.model_validate(r) for r in results],
        passed=passed,
        failed=failed,
        warnings=warnings,
        skipped=skipped,
    )


@router.get("/results/{doc_id}", response_model=ValidationResultList)
def get_validation_results(
    doc_id: int, db: Session = Depends(get_db)
) -> ValidationResultList:
    """Get all validation results for a document."""
    doc_service = DocumentService(db)
    if not doc_service.get(doc_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    service = ValidationService(db)
    results = service.get_validation_results(doc_id)

    return ValidationResultList(
        items=[ValidationResultResponse.model_validate(r) for r in results],
        total=len(results),
    )


@router.get("/summary/{engagement_id}", response_model=ValidationSummary)
def get_validation_summary(
    engagement_id: int, db: Session = Depends(get_db)
) -> ValidationSummary:
    """Get validation summary for an engagement."""
    engagement_service = EngagementService(db)
    if not engagement_service.get(engagement_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    service = ValidationService(db)
    summary = service.get_validation_summary(engagement_id)

    return ValidationSummary(**summary)


@router.post("/run-engagement/{engagement_id}")
def run_engagement_validation(
    engagement_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Run validation on all extracted documents in an engagement.

    This runs in the background.
    """
    engagement_service = EngagementService(db)
    if not engagement_service.get(engagement_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    from app.tasks.validation_tasks import validate_engagement_documents
    background_tasks.add_task(validate_engagement_documents, engagement_id)

    return {
        "message": "Validation queued for all extracted documents in the engagement",
        "engagement_id": engagement_id,
    }


@router.post("/run/client/{client_id}")
def run_client_validation(
    client_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Run validation on all extracted documents for a client.

    Validates all documents across all engagements for the client.
    Uses specialized AI agents for document-specific validation.
    """
    from app.models.clients import Client
    from app.tasks.validation import validate_client_documents

    # Check client exists
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    # Queue validation task
    background_tasks.add_task(validate_client_documents, client_id)

    return {
        "message": f"Validation queued for all documents belonging to client {client.name}",
        "client_id": client_id,
        "client_name": client.name,
    }


@router.post("/reject/{doc_id}")
async def reject_document(
    doc_id: int,
    rejection: DocumentRejectionRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Reject a document and send email notification to client.

    This marks the document as failed and sends an email to the client
    explaining why it was rejected.
    """
    from app.models.documents import DocumentStatus
    from app.services.email_notification_service import EmailNotificationService

    doc_service = DocumentService(db)
    doc = doc_service.get(doc_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Update document status
    doc.status = DocumentStatus.FAILED
    doc.processing_error = f"Rejected by {rejection.rejected_by}: {rejection.rejection_reason}"
    db.commit()

    # Send rejection email
    try:
        email_service = EmailNotificationService(db=db)
        email_sent = await email_service.send_document_rejection_email(
            document_id=doc_id,
            rejected_by=rejection.rejected_by,
            rejection_reason=rejection.rejection_reason,
        )

        return {
            "message": "Document rejected successfully",
            "document_id": doc_id,
            "email_sent": email_sent,
            "rejected_by": rejection.rejected_by,
        }
    except Exception as e:
        # Document is still rejected even if email fails
        return {
            "message": "Document rejected but email notification failed",
            "document_id": doc_id,
            "email_sent": False,
            "error": str(e),
            "rejected_by": rejection.rejected_by,
        }
