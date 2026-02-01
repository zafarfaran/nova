"""API routes for Client management."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.client import (
    ClientCreate,
    ClientList,
    ClientResponse,
    ClientUpdate,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
)
from app.services.audit_service import AuditService
from app.services.client_service import ClientService
from app.services.engagement_service import EngagementService

router = APIRouter(prefix="/clients", tags=["clients"])

logger = logging.getLogger(__name__)


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, db: Session = Depends(get_db)) -> ClientResponse:
    """Create a new client."""
    service = ClientService(db)
    if data.vat_number:
        existing = service.get_by_vat_number(data.vat_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Client with VAT number {data.vat_number} already exists",
            )
    client = service.create(data)
    return ClientResponse.model_validate(client)


@router.get("", response_model=ClientList)
def list_clients(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> ClientList:
    """List all clients."""
    service = ClientService(db)
    clients, total = service.list(skip=skip, limit=limit)
    return ClientList(
        items=[ClientResponse.model_validate(c) for c in clients], total=total
    )


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)) -> ClientResponse:
    """Get a client by ID."""
    service = ClientService(db)
    client = service.get(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return ClientResponse.model_validate(client)


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int, data: ClientUpdate, db: Session = Depends(get_db)
) -> ClientResponse:
    """Update a client."""
    service = ClientService(db)
    client = service.update(client_id, data)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a client.
    
    WARNING: This operation will fail if the client has associated documents or engagements.
    The database enforces RESTRICT constraints to prevent accidental data loss.
    
    For production use, ensure:
    1. Database backups are in place
    2. All documents and engagements are removed or archived first
    3. Consider implementing a soft-delete pattern for production
    """
    service = ClientService(db)
    try:
        if not service.delete(client_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )
    except ValueError as e:
        # Handle validation errors from service layer
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.post(
    "/{client_id}/onboarding-complete", response_model=OnboardingCompleteResponse
)
def onboarding_complete(
    client_id: int,
    data: OnboardingCompleteRequest,
    db: Session = Depends(get_db),
) -> OnboardingCompleteResponse:
    """Handle onboarding completion notifications from the portal."""
    logger.info("Onboarding complete received for client %s", client_id)
    logger.debug("Onboarding payload: %s", data.model_dump())

    if data.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id in path does not match payload",
        )

    client_service = ClientService(db)
    client = client_service.get(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    engagement_id = data.engagement_id if hasattr(data, 'engagement_id') else data.vat_period_id
    if engagement_id is not None:
        engagement_service = EngagementService(db)
        engagement = engagement_service.get(engagement_id)
        if not engagement or engagement.client_id != client_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found for client",
            )

        description = (
            "Onboarding completed."
            f" completed={data.completed_items},"
            f" not_applicable={data.not_applicable_items},"
            f" total={data.total_items}"
        )
        AuditService(db).log(
            engagement_id=engagement.id,
            action="onboarding_complete",
            description=description,
            entity_type="client",
            entity_id=client_id,
        )
        logger.info(
            "Onboarding completion logged for client %s (engagement %s)",
            client_id,
            engagement.id,
        )

    return OnboardingCompleteResponse(
        success=True,
        message="Onboarding completion recorded",
        client_id=client_id,
        engagement_id=engagement_id,
    )
