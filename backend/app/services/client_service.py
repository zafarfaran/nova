"""Service layer for Client operations."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


class ClientService:
    """Service for managing clients."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ClientCreate) -> Client:
        """Create a new client."""
        client = Client(**data.model_dump())
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def get(self, client_id: int) -> Client | None:
        """Get a client by ID."""
        return self.db.get(Client, client_id)

    def get_by_vat_number(self, vat_number: str) -> Client | None:
        """Get a client by VAT number."""
        stmt = select(Client).where(Client.vat_number == vat_number)
        return self.db.scalars(stmt).first()

    def list(self, skip: int = 0, limit: int = 100) -> tuple[list[Client], int]:
        """List all clients with pagination."""
        stmt = select(Client).offset(skip).limit(limit)
        clients = list(self.db.scalars(stmt).all())
        total = self.db.query(func.count(Client.id)).scalar()
        return clients, total or 0

    def update(self, client_id: int, data: ClientUpdate) -> Client | None:
        """Update a client."""
        client = self.get(client_id)
        if not client:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(client, key, value)
        self.db.commit()
        self.db.refresh(client)
        return client

    def delete(self, client_id: int) -> bool:
        """Delete a client."""
        client = self.get(client_id)
        if not client:
            return False
        self.db.delete(client)
        self.db.commit()
        return True

    def search(self, query: str, skip: int = 0, limit: int = 100) -> tuple[list[Client], int]:
        """Search clients by name or VAT number."""
        search_pattern = f"%{query}%"
        stmt = (
            select(Client)
            .where(
                (Client.name.ilike(search_pattern)) |
                (Client.vat_number.ilike(search_pattern)) |
                (Client.display_name.ilike(search_pattern))
            )
            .offset(skip)
            .limit(limit)
        )
        clients = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(func.count(Client.id))
            .filter(
                (Client.name.ilike(search_pattern)) |
                (Client.vat_number.ilike(search_pattern)) |
                (Client.display_name.ilike(search_pattern))
            )
            .scalar()
        )
        return clients, total or 0
