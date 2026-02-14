"""RequestItem model - individual document request items."""

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.requests.set import RequestSet
    from app.models.documents.type import DocumentType
    from app.models.clients.contact import ClientContact
    from app.models.documents.document import Document


class RequestItemStatus(str, enum.Enum):
    """Status of a request item."""
    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETE = "complete"
    WAIVED = "waived"


# Association table for many-to-many relationship between RequestItem and Document
request_item_documents = Table(
    "request_item_documents",
    Base.metadata,
    Column("request_item_id", Integer, ForeignKey("request_items.id"), primary_key=True),
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
)


class RequestItem(Base, TimestampMixin):
    """Request item entity - individual document request.
    
    This replaces ChecklistItem with a more structured request system
    that links to document types and can track multiple documents.
    """

    __tablename__ = "request_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_set_id: Mapped[int] = mapped_column(ForeignKey("request_sets.id"), nullable=False, index=True)
    document_type_id: Mapped[int] = mapped_column(ForeignKey("document_types.id"), nullable=False, index=True)
    
    # Request details
    description: Mapped[str | None] = mapped_column(String(500))
    expected_count: Mapped[int] = mapped_column(Integer, default=1)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[RequestItemStatus] = mapped_column(
        Enum(RequestItemStatus), default=RequestItemStatus.PENDING
    )
    
    # Assignment
    assigned_to_contact_id: Mapped[int | None] = mapped_column(ForeignKey("client_contacts.id"))
    due_date: Mapped[date | None] = mapped_column(Date)
    
    # Relationships
    request_set: Mapped["RequestSet"] = relationship("RequestSet", back_populates="items")
    document_type: Mapped["DocumentType"] = relationship("DocumentType", back_populates="request_items")
    assigned_to: Mapped["ClientContact | None"] = relationship("ClientContact")
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        secondary=request_item_documents,
        back_populates="request_items"
    )

    def __repr__(self) -> str:
        return f"<RequestItem(id={self.id}, status={self.status}, expected={self.expected_count})>"
