"""API routes for Client management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.client import ClientCreate, ClientList, ClientResponse, ClientUpdate
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


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
    """Delete a client."""
    service = ClientService(db)
    if not service.delete(client_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
