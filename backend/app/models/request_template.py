"""RequestTemplate models for reusable document request templates."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document_type import DocumentType


class RequestTemplate(Base, TimestampMixin):
    """Template for creating request sets - reusable document request patterns."""

    __tablename__ = "request_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Template details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_type: Mapped[str | None] = mapped_column(String(50))  # sole_trader, limited_company, or null for all
    engagement_type: Mapped[str | None] = mapped_column(String(50))  # vat_return, annual_accounts, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    items: Mapped[list["RequestTemplateItem"]] = relationship(
        "RequestTemplateItem", back_populates="template", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RequestTemplate(id={self.id}, name='{self.name}')>"


class RequestTemplateItem(Base, TimestampMixin):
    """Individual item in a request template."""

    __tablename__ = "request_template_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("request_templates.id"), nullable=False, index=True)
    document_type_id: Mapped[int] = mapped_column(ForeignKey("document_types.id"), nullable=False, index=True)
    
    # Item details
    description: Mapped[str | None] = mapped_column(String(500))
    expected_count: Mapped[int] = mapped_column(Integer, default=1)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    template: Mapped["RequestTemplate"] = relationship("RequestTemplate", back_populates="items")
    document_type: Mapped["DocumentType"] = relationship("DocumentType", back_populates="request_template_items")

    def __repr__(self) -> str:
        return f"<RequestTemplateItem(id={self.id}, template_id={self.template_id})>"
