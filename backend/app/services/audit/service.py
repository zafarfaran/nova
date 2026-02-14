"""Service layer for Audit Log operations."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditService:
    """Service for managing audit logs."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        client_id: int | None = None,
        engagement_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        action: str = "",
        actor_contact_id: int | None = None,
        changes: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Add an entry to the audit log."""
        entry = AuditLog(
            client_id=client_id,
            engagement_id=engagement_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_contact_id=actor_contact_id,
            changes=changes or {},
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_by_engagement(
        self, engagement_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[AuditLog], int]:
        """Get audit logs for an engagement."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.engagement_id == engagement_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        entries = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(func.count(AuditLog.id))
            .filter(AuditLog.engagement_id == engagement_id)
            .scalar()
        )
        return entries, total or 0

    def get_by_client(
        self, client_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[AuditLog], int]:
        """Get audit logs for a client."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.client_id == client_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        entries = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(func.count(AuditLog.id))
            .filter(AuditLog.client_id == client_id)
            .scalar()
        )
        return entries, total or 0

    def get_by_entity(
        self, entity_type: str, entity_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[AuditLog], int]:
        """Get audit logs for a specific entity."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        entries = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(func.count(AuditLog.id))
            .filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .scalar()
        )
        return entries, total or 0
