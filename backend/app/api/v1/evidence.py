"""API routes for Evidence management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.evidence import (
    CoverageSummary,
    EvidenceItemCreate,
    EvidenceItemList,
    EvidenceItemResponse,
    EvidenceItemUpdate,
    GapReport,
)
from app.services.client_service import VATPeriodService
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post(
    "", response_model=EvidenceItemResponse, status_code=status.HTTP_201_CREATED
)
def create_evidence_item(
    data: EvidenceItemCreate, db: Session = Depends(get_db)
) -> EvidenceItemResponse:
    """Create a new evidence item."""
    period_service = VATPeriodService(db)
    if not period_service.get(data.vat_period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    service = EvidenceService(db)
    item = service.create(data)
    return EvidenceItemResponse.model_validate(item)


@router.get("", response_model=EvidenceItemList)
def list_evidence_items(
    vat_period_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> EvidenceItemList:
    """List all evidence items for a VAT period."""
    service = EvidenceService(db)
    items, total = service.list_by_period(vat_period_id, skip=skip, limit=limit)
    return EvidenceItemList(
        items=[EvidenceItemResponse.model_validate(i) for i in items], total=total
    )


@router.get("/{item_id}", response_model=EvidenceItemResponse)
def get_evidence_item(
    item_id: int, db: Session = Depends(get_db)
) -> EvidenceItemResponse:
    """Get an evidence item by ID."""
    service = EvidenceService(db)
    item = service.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence item not found"
        )
    return EvidenceItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=EvidenceItemResponse)
def update_evidence_item(
    item_id: int, data: EvidenceItemUpdate, db: Session = Depends(get_db)
) -> EvidenceItemResponse:
    """Update an evidence item."""
    service = EvidenceService(db)
    item = service.update(item_id, data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence item not found"
        )
    return EvidenceItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence_item(item_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an evidence item."""
    service = EvidenceService(db)
    if not service.delete(item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence item not found"
        )


@router.post("/schedule/{period_id}/build", response_model=EvidenceItemList)
def build_evidence_schedule(
    period_id: int,
    include_optional: bool = False,
    db: Session = Depends(get_db),
) -> EvidenceItemList:
    """Build evidence schedule for a VAT period."""
    period_service = VATPeriodService(db)
    if not period_service.get(period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    service = EvidenceService(db)
    try:
        items = service.build_schedule(period_id, include_optional=include_optional)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return EvidenceItemList(
        items=[EvidenceItemResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.get("/coverage/{period_id}", response_model=CoverageSummary)
def get_coverage(period_id: int, db: Session = Depends(get_db)) -> CoverageSummary:
    """Get coverage metrics for a VAT period."""
    period_service = VATPeriodService(db)
    if not period_service.get(period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    service = EvidenceService(db)
    return service.get_coverage(period_id)


@router.get("/gaps/{period_id}", response_model=GapReport)
def get_gaps(period_id: int, db: Session = Depends(get_db)) -> GapReport:
    """Get gaps report for a VAT period."""
    period_service = VATPeriodService(db)
    if not period_service.get(period_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )

    service = EvidenceService(db)
    return service.get_gaps(period_id)
