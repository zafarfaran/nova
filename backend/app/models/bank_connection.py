"""BankConnection model for Plaid bank integrations."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client


class BankConnection(Base, TimestampMixin):
    """Bank connection via Plaid - linked to clients table."""

    __tablename__ = "bank_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    plaid_access_token: Mapped[str] = mapped_column(String(255), nullable=False)
    plaid_item_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_mask: Mapped[str | None] = mapped_column(String(10))
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    account_subtype: Mapped[str | None] = mapped_column(String(50))
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="bank_connections")

    def __repr__(self) -> str:
        return f"<BankConnection(id={self.id}, institution_name='{self.institution_name}')>"
