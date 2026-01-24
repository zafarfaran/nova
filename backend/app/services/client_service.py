"""Service layer for Client operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.vat_period import VATPeriod
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.vat_period import VATPeriodCreate, VATPeriodUpdate


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
        total = self.db.query(Client).count()
        return clients, total

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


class VATPeriodService:
    """Service for managing VAT periods."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: VATPeriodCreate) -> VATPeriod:
        """Create a new VAT period."""
        vat_period = VATPeriod(**data.model_dump())
        self.db.add(vat_period)
        self.db.commit()
        self.db.refresh(vat_period)
        return vat_period

    def get(self, period_id: int) -> VATPeriod | None:
        """Get a VAT period by ID."""
        return self.db.get(VATPeriod, period_id)

    def list_by_client(
        self, client_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[VATPeriod], int]:
        """List all VAT periods for a client."""
        stmt = (
            select(VATPeriod)
            .where(VATPeriod.client_id == client_id)
            .offset(skip)
            .limit(limit)
        )
        periods = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(VATPeriod).filter(VATPeriod.client_id == client_id).count()
        )
        return periods, total

    def update(self, period_id: int, data: VATPeriodUpdate) -> VATPeriod | None:
        """Update a VAT period."""
        period = self.get(period_id)
        if not period:
            return None
        if period.is_locked:
            raise ValueError("Cannot update a locked VAT period")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(period, key, value)
        self.db.commit()
        self.db.refresh(period)
        return period

    def delete(self, period_id: int) -> bool:
        """Delete a VAT period."""
        period = self.get(period_id)
        if not period:
            return False
        if period.is_locked:
            raise ValueError("Cannot delete a locked VAT period")
        self.db.delete(period)
        self.db.commit()
        return True

    def lock(self, period_id: int) -> VATPeriod | None:
        """Lock a VAT period."""
        period = self.get(period_id)
        if not period:
            return None
        period.is_locked = True
        self.db.commit()
        self.db.refresh(period)
        return period
