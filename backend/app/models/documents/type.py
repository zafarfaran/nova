"""DocumentCategory and DocumentType models for configurable document types."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.documents.document import Document
    from app.models.requests.item import RequestItem
    from app.models.requests.template import RequestTemplateItem


class DocumentCategory(Base, TimestampMixin):
    """Category for grouping document types."""

    __tablename__ = "document_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    document_types: Mapped[list["DocumentType"]] = relationship(
        "DocumentType", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DocumentCategory(id={self.id}, code='{self.code}', name='{self.name}')>"


class DocumentType(Base, TimestampMixin):
    """Configurable document type - replaces the DocumentType enum."""

    __tablename__ = "document_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("document_categories.id"), nullable=False, index=True)
    
    # Type details
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Scoping - which client types need this doc type
    client_type_scope: Mapped[str | None] = mapped_column(String(50))  # sole_trader, limited_company, or null for all
    
    # Requirements
    requires_counterparty: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_account: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_engagement: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Retention
    retention_years: Mapped[int] = mapped_column(Integer, default=7)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    category: Mapped["DocumentCategory"] = relationship("DocumentCategory", back_populates="document_types")
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="document_type", cascade="all, delete-orphan"
    )
    request_items: Mapped[list["RequestItem"]] = relationship(
        "RequestItem", back_populates="document_type", cascade="all, delete-orphan"
    )
    request_template_items: Mapped[list["RequestTemplateItem"]] = relationship(
        "RequestTemplateItem", back_populates="document_type", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DocumentType(id={self.id}, code='{self.code}', name='{self.name}')>"
