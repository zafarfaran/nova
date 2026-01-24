"""API routes for Audit Trail."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.audit import AuditTrailEntryResponse, AuditTrailList
from app.services.audit_service import AuditService
from app.services.client_service import VATPeriodService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/trail/{period_id}", response_model=AuditTrailList)
def get_audit_trail(
    period_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> AuditTrailList:
    """Get audit trail for a VAT period."""
    period_service = VATPeriodService(db)
    if not period_service.get(period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    service = AuditService(db)
    entries, total = service.get_trail(period_id, skip=skip, limit=limit)
    return AuditTrailList(
        items=[AuditTrailEntryResponse.model_validate(e) for e in entries], total=total
    )
