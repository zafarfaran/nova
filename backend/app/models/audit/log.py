"""AuditLog model - unified audit trail replacing AuditTrailEntry."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base

if TYPE_CHECKING:
    from app.models.clients.client import Client
    from app.models.engagements.engagement import Engagement
    from app.models.clients.contact import ClientContact


class AuditLog(Base):
    """Unified audit log for tracking all system changes.
    
    This replaces AuditTrailEntry with a more flexible audit system
    that can track changes across all entity types.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Context
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), index=True)
    engagement_id: Mapped[int | None] = mapped_column(ForeignKey("engagements.id"), index=True)
    
    # Entity being modified
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # document, client, etc.
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Action details
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # create, update, delete, etc.
    actor_contact_id: Mapped[int | None] = mapped_column(ForeignKey("client_contacts.id"))
    
    # Change details
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # {field: {old: x, new: y}}
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    client: Mapped["Client | None"] = relationship("Client", back_populates="audit_logs")
    engagement: Mapped["Engagement | None"] = relationship("Engagement", back_populates="audit_logs")
    actor: Mapped["ClientContact | None"] = relationship("ClientContact")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, entity={self.entity_type}:{self.entity_id}, action='{self.action}')>"
