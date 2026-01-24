"""Service layer for Audit Trail operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditTrailEntry


class AuditService:
    """Service for managing audit trail."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        period_id: int,
        action: str,
        description: str | None = None,
        performed_by: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> AuditTrailEntry:
        """Add an entry to the audit trail."""
        entry = AuditTrailEntry(
            vat_period_id=period_id,
            action=action,
            description=description,
            performed_by=performed_by,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_trail(
        self, period_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[AuditTrailEntry], int]:
        """Get audit trail for a VAT period."""
        stmt = (
            select(AuditTrailEntry)
            .where(AuditTrailEntry.vat_period_id == period_id)
            .order_by(AuditTrailEntry.performed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        entries = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(AuditTrailEntry)
            .filter(AuditTrailEntry.vat_period_id == period_id)
            .count()
        )
        return entries, total
