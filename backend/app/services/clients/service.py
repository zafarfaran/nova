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
        """Create a new client and optionally create an engagement."""
        from app.services.engagements import EngagementService
        from app.schemas.engagements.engagement import EngagementCreate
        
        # Extract engagement data if provided
        engagement_data = None
        if data.engagement:
            engagement_data = data.engagement
        
        # Create client without engagement field
        client_dict = data.model_dump(exclude={'engagement'})
        client = Client(**client_dict)
        self.db.add(client)
        self.db.flush()  # Get client ID without committing
        
        # Create engagement if provided
        if engagement_data:
            engagement_service = EngagementService(self.db)
            engagement_create = engagement_data.model_dump()
            engagement_create['client_id'] = client.id
            engagement = engagement_service.create(EngagementCreate(**engagement_create))
            self.db.flush()
        
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
        """Delete a client.
        
        WARNING: This operation is restricted if the client has associated documents.
        The database will prevent deletion if documents exist (RESTRICT constraint).
        
        For production use, consider:
        1. Creating a database backup before deletion
        2. Implementing a soft-delete pattern
        3. Manually removing or archiving documents first
        
        Raises:
            IntegrityError: If client has associated documents or other dependent records.
        """
        from sqlalchemy import func, select
        from sqlalchemy.exc import IntegrityError
        from app.models.documents import Document
        from app.models.engagements import Engagement
        
        client = self.get(client_id)
        if not client:
            return False
        
        # Check for dependent records before attempting deletion
        # This provides a clearer error message than database constraint violation
        doc_count = self.db.scalar(
            select(func.count(Document.id)).where(Document.client_id == client_id)
        ) or 0
        
        engagement_count = self.db.scalar(
            select(func.count(Engagement.id)).where(Engagement.client_id == client_id)
        ) or 0
        
        if doc_count > 0:
            raise ValueError(
                f"Cannot delete client {client_id}: {doc_count} document(s) exist. "
                "Please remove or archive documents first, or use a soft-delete pattern."
            )
        
        if engagement_count > 0:
            raise ValueError(
                f"Cannot delete client {client_id}: {engagement_count} engagement(s) exist. "
                "Please remove engagements first."
            )
        
        try:
            self.db.delete(client)
            self.db.commit()
            return True
        except IntegrityError as e:
            # Database-level constraint violation (additional safety)
            self.db.rollback()
            raise ValueError(
                f"Cannot delete client {client_id}: database constraint violation. "
                "This client has dependent records that must be removed first."
            ) from e

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
