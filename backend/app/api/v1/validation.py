"""API routes for document validation."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.validation import ValidationStatus
from app.schemas.validation import (
    ValidationResultList,
    ValidationResultResponse,
    ValidationRunResponse,
    ValidationSummary,
)
from app.services.client_service import VATPeriodService
from app.services.document_service import DocumentService
from app.services.validation_service import ValidationService
from app.tasks.validation_tasks import validate_period_documents

router = APIRouter(prefix="/validation", tags=["validation"])


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


@router.get("/summary/{period_id}", response_model=ValidationSummary)
def get_validation_summary(
    period_id: int, db: Session = Depends(get_db)
) -> ValidationSummary:
    """Get validation summary for a VAT period."""
    period_service = VATPeriodService(db)
    if not period_service.get(period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    service = ValidationService(db)
    summary = service.get_validation_summary(period_id)

    return ValidationSummary(**summary)


@router.post("/run-period/{period_id}")
def run_period_validation(
    period_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Run validation on all extracted documents in a VAT period.

    This runs in the background.
    """
    period_service = VATPeriodService(db)
    if not period_service.get(period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    background_tasks.add_task(validate_period_documents, period_id)

    return {
        "message": "Validation queued for all extracted documents in the period",
        "vat_period_id": period_id,
    }


@router.post("/run/client/{client_id}")
def run_client_validation(
    client_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Run validation on all extracted documents for a client.

    Validates all documents across all VAT periods for the client.
    Uses specialized AI agents for document-specific validation.
    """
    from sqlalchemy import select
    from app.models.client import Client
    from app.models.vat_period import VATPeriod
    from app.tasks.validation_tasks import validate_client_documents

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
