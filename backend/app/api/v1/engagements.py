"""API routes for Engagements."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.engagement import (
    EngagementCreate,
    EngagementList,
    EngagementResponse,
    EngagementUpdate,
)
from app.services.client_service import ClientService
from app.services.engagement_service import EngagementService

router = APIRouter(prefix="/engagements", tags=["engagements"])


@router.post("", response_model=EngagementResponse, status_code=status.HTTP_201_CREATED)
def create_engagement(
    data: EngagementCreate, db: Session = Depends(get_db)
) -> EngagementResponse:
    """Create a new engagement."""
    client_service = ClientService(db)
    if not client_service.get(data.client_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    service = EngagementService(db)
    engagement = service.create(data)
    return EngagementResponse.model_validate(engagement)


@router.get("", response_model=EngagementList)
def list_engagements(
    client_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> EngagementList:
    """List engagements for a client."""
    client_service = ClientService(db)
    if not client_service.get(client_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    service = EngagementService(db)
    engagements, total = service.list_by_client(client_id, skip=skip, limit=limit)
    return EngagementList(
        items=[EngagementResponse.model_validate(e) for e in engagements], total=total
    )


@router.get("/{engagement_id}", response_model=EngagementResponse)
def get_engagement(
    engagement_id: int, db: Session = Depends(get_db)
) -> EngagementResponse:
    """Get an engagement by ID."""
    service = EngagementService(db)
    engagement = service.get(engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )
    return EngagementResponse.model_validate(engagement)


@router.patch("/{engagement_id}", response_model=EngagementResponse)
def update_engagement(
    engagement_id: int, data: EngagementUpdate, db: Session = Depends(get_db)
) -> EngagementResponse:
    """Update an engagement."""
    service = EngagementService(db)
    engagement = service.update(engagement_id, data)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found or is locked",
        )
    return EngagementResponse.model_validate(engagement)


@router.delete("/{engagement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_engagement(engagement_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an engagement."""
    service = EngagementService(db)
    if not service.delete(engagement_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found or is locked",
        )


@router.post("/{engagement_id}/lock", response_model=EngagementResponse)
def lock_engagement(
    engagement_id: int, db: Session = Depends(get_db)
) -> EngagementResponse:
    """Lock an engagement."""
    service = EngagementService(db)
    engagement = service.lock(engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )
    return EngagementResponse.model_validate(engagement)


@router.post("/{engagement_id}/unlock", response_model=EngagementResponse)
def unlock_engagement(
    engagement_id: int, db: Session = Depends(get_db)
) -> EngagementResponse:
    """Unlock an engagement."""
    service = EngagementService(db)
    engagement = service.unlock(engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )
    return EngagementResponse.model_validate(engagement)
