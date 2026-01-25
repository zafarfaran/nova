"""API routes for Chaser management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chaser import (
    AutoChaseRequest,
    ChaserRequestCreate,
    ChaserRequestList,
    ChaserRequestResponse,
    ChaserResponseCreate,
    ChaserResponseResponse,
)
from app.services.chaser_service import ChaserService
from app.services.client_service import VATPeriodService

router = APIRouter(prefix="/chaser", tags=["chaser"])


@router.post(
    "/requests", response_model=ChaserRequestResponse, status_code=status.HTTP_201_CREATED
)
def create_chaser_request(
    data: ChaserRequestCreate, db: Session = Depends(get_db)
) -> ChaserRequestResponse:
    """Create a new chaser request."""
    period_service = VATPeriodService(db)
    if not period_service.get(data.vat_period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    service = ChaserService(db)
    chaser = service.create(
        vat_period_id=data.vat_period_id,
        recipient_email=data.recipient_email,
        recipient_name=data.recipient_name,
        requested_items=data.requested_items,
        due_date=data.due_date,
    )
    return ChaserRequestResponse.model_validate(chaser)


@router.get("/requests", response_model=ChaserRequestList)
def list_chaser_requests(
    vat_period_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> ChaserRequestList:
    """List all chaser requests for a VAT period."""
    service = ChaserService(db)
    chasers, total = service.list_by_period(vat_period_id, skip=skip, limit=limit)
    return ChaserRequestList(
        items=[ChaserRequestResponse.model_validate(c) for c in chasers], total=total
    )


@router.get("/requests/{chaser_id}", response_model=ChaserRequestResponse)
def get_chaser_request(
    chaser_id: int, db: Session = Depends(get_db)
) -> ChaserRequestResponse:
    """Get a chaser request by ID."""
    service = ChaserService(db)
    chaser = service.get(chaser_id)
    if not chaser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chaser request not found"
        )
    return ChaserRequestResponse.model_validate(chaser)


@router.post("/requests/{chaser_id}/generate-message", response_model=ChaserRequestResponse)
async def generate_chaser_message(
    chaser_id: int, db: Session = Depends(get_db)
) -> ChaserRequestResponse:
    """Generate AI message for a chaser request."""
    service = ChaserService(db)
    chaser = await service.generate_message(chaser_id)
    if not chaser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chaser request not found"
        )
    return ChaserRequestResponse.model_validate(chaser)


@router.post("/requests/{chaser_id}/send-email", response_model=ChaserRequestResponse)
async def send_chaser_email(
    chaser_id: int, db: Session = Depends(get_db)
) -> ChaserRequestResponse:
    """Generate and send the chaser email to the client.

    This will:
    1. Generate the message if not already generated
    2. Send the email via SMTP
    3. Mark the chaser as sent
    """
    service = ChaserService(db)
    chaser = await service.send_chaser_email(chaser_id)
    if not chaser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chaser request not found"
        )
    return ChaserRequestResponse.model_validate(chaser)


@router.post("/requests/{chaser_id}/send", response_model=ChaserRequestResponse)
def send_chaser_request(
    chaser_id: int, db: Session = Depends(get_db)
) -> ChaserRequestResponse:
    """Mark a chaser request as sent (without actually sending email).

    Use /send-email endpoint to actually send the email.
    """
    service = ChaserService(db)
    chaser = service.mark_sent(chaser_id)
    if not chaser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chaser request not found"
        )
    return ChaserRequestResponse.model_validate(chaser)


@router.post("/requests/{chaser_id}/remind", response_model=ChaserRequestResponse)
def remind_chaser_request(
    chaser_id: int, db: Session = Depends(get_db)
) -> ChaserRequestResponse:
    """Mark a chaser request as reminded."""
    service = ChaserService(db)
    chaser = service.mark_reminded(chaser_id)
    if not chaser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chaser request not found"
        )
    return ChaserRequestResponse.model_validate(chaser)


@router.post("/auto-chase/{period_id}", response_model=ChaserRequestResponse)
def auto_chase(
    period_id: int, data: AutoChaseRequest, db: Session = Depends(get_db)
) -> ChaserRequestResponse:
    """Automatically create a chaser for all gaps in a VAT period."""
    period_service = VATPeriodService(db)
    if not period_service.get(period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    service = ChaserService(db)
    chaser = service.auto_chase(period_id, data.recipient_email)
    if not chaser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No gaps found to chase",
        )
    return ChaserRequestResponse.model_validate(chaser)


@router.get("/by-token/{upload_token}", response_model=ChaserRequestResponse)
def get_chaser_by_token(
    upload_token: str, db: Session = Depends(get_db)
) -> ChaserRequestResponse:
    """Get a chaser request by upload token (for document upload)."""
    service = ChaserService(db)
    chaser = service.get_by_token(upload_token)
    if not chaser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid upload token"
        )
    return ChaserRequestResponse.model_validate(chaser)


@router.post(
    "/requests/{chaser_id}/response",
    response_model=ChaserResponseResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_chaser_response(
    chaser_id: int, data: ChaserResponseCreate, db: Session = Depends(get_db)
) -> ChaserResponseResponse:
    """Record a response to a chaser request."""
    service = ChaserService(db)
    if not service.get(chaser_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chaser request not found"
        )

    response = service.record_response(
        chaser_id=chaser_id,
        documents_uploaded=data.documents_uploaded,
        responder_email=data.responder_email,
        responder_name=data.responder_name,
        notes=data.notes,
    )
    return ChaserResponseResponse.model_validate(response)
