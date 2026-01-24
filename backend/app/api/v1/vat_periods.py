"""API routes for VAT Period management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vat_period import (
    VATPeriodCreate,
    VATPeriodList,
    VATPeriodResponse,
    VATPeriodUpdate,
)
from app.services.client_service import ClientService, VATPeriodService

router = APIRouter(prefix="/vat-periods", tags=["vat-periods"])


@router.post("", response_model=VATPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_vat_period(
    data: VATPeriodCreate, db: Session = Depends(get_db)
) -> VATPeriodResponse:
    """Create a new VAT period."""
    client_service = ClientService(db)
    if not client_service.get(data.client_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    if data.period_end <= data.period_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period end must be after period start",
        )

    service = VATPeriodService(db)
    period = service.create(data)
    return VATPeriodResponse.model_validate(period)


@router.get("", response_model=VATPeriodList)
def list_vat_periods(
    client_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> VATPeriodList:
    """List all VAT periods for a client."""
    client_service = ClientService(db)
    if not client_service.get(client_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    service = VATPeriodService(db)
    periods, total = service.list_by_client(client_id, skip=skip, limit=limit)
    return VATPeriodList(
        items=[VATPeriodResponse.model_validate(p) for p in periods], total=total
    )


@router.get("/{period_id}", response_model=VATPeriodResponse)
def get_vat_period(period_id: int, db: Session = Depends(get_db)) -> VATPeriodResponse:
    """Get a VAT period by ID."""
    service = VATPeriodService(db)
    period = service.get(period_id)
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )
    return VATPeriodResponse.model_validate(period)


@router.patch("/{period_id}", response_model=VATPeriodResponse)
def update_vat_period(
    period_id: int, data: VATPeriodUpdate, db: Session = Depends(get_db)
) -> VATPeriodResponse:
    """Update a VAT period."""
    service = VATPeriodService(db)
    try:
        period = service.update(period_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )
    return VATPeriodResponse.model_validate(period)


@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vat_period(period_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a VAT period."""
    service = VATPeriodService(db)
    try:
        if not service.delete(period_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{period_id}/lock", response_model=VATPeriodResponse)
def lock_vat_period(
    period_id: int, db: Session = Depends(get_db)
) -> VATPeriodResponse:
    """Lock a VAT period."""
    service = VATPeriodService(db)
    period = service.lock(period_id)
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VAT period not found"
        )
    return VATPeriodResponse.model_validate(period)
