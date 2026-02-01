"""Service layer for Engagement operations."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.schemas.engagement import EngagementCreate, EngagementUpdate
from app.services.audit_service import AuditService


class EngagementService:
    """Service for managing engagements."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: EngagementCreate) -> Engagement:
        """Create a new engagement."""
        engagement = Engagement(**data.model_dump())
        self.db.add(engagement)
        self.db.commit()
        self.db.refresh(engagement)
        return engagement

    def get(self, engagement_id: int) -> Engagement | None:
        """Get an engagement by ID."""
        return self.db.get(Engagement, engagement_id)

    def list_by_client(
        self, client_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[Engagement], int]:
        """List engagements for a client."""
        stmt = (
            select(Engagement)
            .where(Engagement.client_id == client_id)
            .order_by(Engagement.period_end.desc())
            .offset(skip)
            .limit(limit)
        )
        engagements = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(func.count(Engagement.id))
            .filter(Engagement.client_id == client_id)
            .scalar()
        )
        return engagements, total or 0

    def update(self, engagement_id: int, data: EngagementUpdate) -> Engagement | None:
        """Update an engagement."""
        engagement = self.get(engagement_id)
        if not engagement:
            return None

        if engagement.is_locked:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(engagement, field, value)

        self.db.commit()
        self.db.refresh(engagement)
        return engagement

    def delete(self, engagement_id: int) -> bool:
        """Delete an engagement."""
        engagement = self.get(engagement_id)
        if not engagement:
            return False

        if engagement.is_locked:
            return False

        self.db.delete(engagement)
        self.db.commit()
        return True

    def lock(
        self, engagement_id: int, actor_contact_id: int | None = None
    ) -> Engagement | None:
        """Lock an engagement."""
        engagement = self.get(engagement_id)
        if not engagement:
            return None

        # Track old value for audit logging
        old_value = engagement.is_locked
        
        # If already locked, no change needed
        if old_value:
            return engagement

        engagement.is_locked = True
        self.db.commit()
        self.db.refresh(engagement)

        # Log the lock action
        AuditService(self.db).log(
            client_id=engagement.client_id,
            engagement_id=engagement.id,
            entity_type="engagement",
            entity_id=engagement.id,
            action="lock",
            actor_contact_id=actor_contact_id,
            changes={"is_locked": {"old": old_value, "new": True}},
        )

        return engagement

    def unlock(
        self, engagement_id: int, actor_contact_id: int | None = None
    ) -> Engagement | None:
        """Unlock an engagement."""
        engagement = self.get(engagement_id)
        if not engagement:
            return None

        # Track old value for audit logging
        old_value = engagement.is_locked
        
        # If already unlocked, no change needed
        if not old_value:
            return engagement

        engagement.is_locked = False
        self.db.commit()
        self.db.refresh(engagement)

        # Log the unlock action
        AuditService(self.db).log(
            client_id=engagement.client_id,
            engagement_id=engagement.id,
            entity_type="engagement",
            entity_id=engagement.id,
            action="unlock",
            actor_contact_id=actor_contact_id,
            changes={"is_locked": {"old": old_value, "new": False}},
        )

        return engagement
