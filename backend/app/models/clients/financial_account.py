"""FinancialAccount model - replaces BankConnection with broader account support."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.clients.client import Client
    from app.models.documents.document import Document


class AccountType(str, enum.Enum):
    """Type of financial account."""
    BANK_CURRENT = "bank_current"
    BANK_SAVINGS = "bank_savings"
    CREDIT_CARD = "credit_card"
    PAYMENT_PROCESSOR = "payment_processor"  # Stripe, PayPal, etc.
    MERCHANT = "merchant"
    OTHER = "other"


class FinancialAccount(Base, TimestampMixin):
    """Financial account entity - broader than just bank connections.
    
    This replaces BankConnection with support for various account types
    including bank accounts, credit cards, and payment processors.
    """

    __tablename__ = "financial_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    
    # Account details
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)  # Bank name or provider
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="GBP")
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Integration details (optional - for connected accounts)
    plaid_access_token: Mapped[str | None] = mapped_column(String(255))
    plaid_item_id: Mapped[str | None] = mapped_column(String(100))
    account_id: Mapped[str | None] = mapped_column(String(100))
    account_mask: Mapped[str | None] = mapped_column(String(10))
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="financial_accounts")
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FinancialAccount(id={self.id}, name='{self.account_name}', type={self.account_type})>"
