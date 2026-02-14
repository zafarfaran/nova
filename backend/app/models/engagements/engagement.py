"""Engagement model - replaces VATPeriod with a more generic engagement concept."""

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.clients.client import Client
    from app.models.documents.document import Document
    from app.models.requests.set import RequestSet
    from app.models.audit.log import AuditLog
    from app.models.chaser.chaser import ChaserRequest


class EngagementType(str, enum.Enum):
    """Type of engagement."""
    VAT_RETURN = "vat_return"
    ANNUAL_ACCOUNTS = "annual_accounts"
    TAX_RETURN = "tax_return"
    AUDIT = "audit"
    BOOKKEEPING = "bookkeeping"
    OTHER = "other"


class EngagementStatus(str, enum.Enum):
    """Status of an engagement."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    READY = "ready"
    SUBMITTED = "submitted"
    LOCKED = "locked"


class EnumValueType(TypeDecorator):
    """TypeDecorator that ensures enum values (not names) are stored in the database.
    
    This wraps SQLAlchemy's Enum type to store enum values instead of enum names.
    """
    impl = Enum
    cache_ok = True
    
    def __init__(self, enum_class, *args, **kwargs):
        # Create the underlying Enum type with native_enum=True for PostgreSQL
        # but we'll override process_bind_param to store values
        self.enum_class = enum_class
        # Get the enum values for the PostgreSQL ENUM type
        enum_values = [e.value for e in enum_class]
        # Initialize parent Enum with the enum values
        super().__init__(*enum_values, name=kwargs.pop('name', None), native_enum=True, create_type=False, *args, **kwargs)
    
    def process_bind_param(self, value, dialect):
        """Convert enum object to its value string when saving to database."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            # Return the enum value, not the name
            return value.value
        # If it's already a string, return it as-is (assume it's a value)
        return value
    
    def process_result_value(self, value, dialect):
        """Convert value string back to enum object when loading from database."""
        if value is None:
            return None
        # Try to find enum member by value
        for enum_member in self.enum_class:
            if enum_member.value == value:
                return enum_member
        # Fallback: try to create from value
        try:
            return self.enum_class(value)
        except ValueError:
            # If value doesn't match, try to find by name (for backwards compatibility)
            for enum_member in self.enum_class:
                if enum_member.name == value:
                    return enum_member
            raise


class Engagement(Base, TimestampMixin):
    """Engagement entity - represents a specific work engagement for a client.
    
    This replaces VATPeriod with a more flexible engagement model that can
    represent VAT returns, annual accounts, tax returns, or any other engagement.
    """

    __tablename__ = "engagements"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    
    # Engagement details
    engagement_type: Mapped[EngagementType] = mapped_column(
        EnumValueType(EngagementType, name='engagementtype'), 
        default=EngagementType.VAT_RETURN
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[EngagementStatus] = mapped_column(
        EnumValueType(EngagementStatus, name='engagementstatus'), 
        default=EngagementStatus.DRAFT
    )
    
    # Optional metadata
    reference: Mapped[str | None] = mapped_column(String(100))
    due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(String(2000))
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="engagements")
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="engagement", cascade="all, delete-orphan"
    )
    request_sets: Mapped[list["RequestSet"]] = relationship(
        "RequestSet", back_populates="engagement", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="engagement", cascade="all, delete-orphan"
    )
    chaser_requests: Mapped[list["ChaserRequest"]] = relationship(
        "ChaserRequest", back_populates="engagement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Engagement(id={self.id}, type={self.engagement_type}, period={self.period_start}-{self.period_end})>"
