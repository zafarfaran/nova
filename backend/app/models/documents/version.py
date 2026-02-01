"""DocumentVersion model for tracking document versions and AI extraction results."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base

if TYPE_CHECKING:
    from app.models.documents.document import Document
    from app.models.documents.file_object import FileObject
    from app.models.clients.contact import ClientContact


class ExtractionStatus(str, enum.Enum):
    """Status of AI extraction for a document version."""
    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    FAILED = "failed"


class DocumentVersion(Base):
    """Version tracking for documents with AI extraction results.
    
    This is the critical table for AI features - it stores the extracted_data
    that was previously on the Document model directly.
    """

    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_no", name="uq_document_versions_document_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    file_object_id: Mapped[int] = mapped_column(ForeignKey("file_objects.id"), nullable=False, index=True)
    
    # Version tracking
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    uploaded_by_contact_id: Mapped[int | None] = mapped_column(ForeignKey("client_contacts.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # AI Extraction results - CRITICAL FOR AI FEATURES
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus), default=ExtractionStatus.PENDING
    )
    
    # Processing metadata
    processing_error: Mapped[str | None] = mapped_column(String(2000))
    notes: Mapped[str | None] = mapped_column(String(2000))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="versions")
    file_object: Mapped["FileObject"] = relationship("FileObject", back_populates="document_versions")
    uploaded_by: Mapped["ClientContact | None"] = relationship("ClientContact")

    def __repr__(self) -> str:
        return f"<DocumentVersion(id={self.id}, document_id={self.document_id}, version={self.version_no})>"
