"""SQLAlchemy models mapping to Prisma schema for ClientSetup and related tables."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Integer, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    pass


class ClientSetup(Base):
    """Client setup entity - maps to Prisma ClientSetup table."""

    __tablename__ = "ClientSetup"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    clientName: Mapped[str] = mapped_column(String(255), nullable=False)
    entityType: Mapped[str] = mapped_column(String(50), nullable=False)
    vatScheme: Mapped[str] = mapped_column(String(50), nullable=False)
    vatPeriodStart: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vatPeriodEnd: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vatPeriodLabel: Mapped[str] = mapped_column(String(100), nullable=False)
    bankAccounts: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    salesChannels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    backendClientId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    checklistItems: Mapped[list["ChecklistItem"]] = relationship(
        "ChecklistItem", back_populates="clientSetup", cascade="all, delete-orphan"
    )
    autoChasers: Mapped[list["AutoChaser"]] = relationship(
        "AutoChaser", back_populates="clientSetup", cascade="all, delete-orphan"
    )
    bankConnections: Mapped[list["BankConnection"]] = relationship(
        "BankConnection", back_populates="clientSetup", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ClientSetup(id={self.id}, clientName='{self.clientName}', email='{self.email}')>"


class ChecklistItem(Base):
    """Checklist item for document tracking - maps to Prisma ChecklistItem table."""

    __tablename__ = "ChecklistItem"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    clientSetupId: Mapped[str] = mapped_column(
        String(30), ForeignKey("ClientSetup.id", ondelete="CASCADE"), nullable=False
    )
    itemId: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # missing, uploaded, unknown
    acceptance: Mapped[str] = mapped_column(String(50), nullable=False)
    ctaAction: Mapped[str] = mapped_column(String(50), nullable=False)
    ctaData: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploadedFileUrl: Mapped[str | None] = mapped_column(String(500), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    clientSetup: Mapped["ClientSetup"] = relationship("ClientSetup", back_populates="checklistItems")

    def __repr__(self) -> str:
        return f"<ChecklistItem(id={self.id}, title='{self.title}', status='{self.status}')>"


class AutoChaser(Base):
    """Auto chaser for reminder emails - maps to Prisma AutoChaser table."""

    __tablename__ = "AutoChaser"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    clientSetupId: Mapped[str] = mapped_column(
        String(30), ForeignKey("ClientSetup.id", ondelete="CASCADE"), nullable=False
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    delayDays: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    clientSetup: Mapped["ClientSetup"] = relationship("ClientSetup", back_populates="autoChasers")

    def __repr__(self) -> str:
        return f"<AutoChaser(id={self.id}, trigger='{self.trigger}')>"


class BankConnection(Base):
    """Bank connection via Plaid - maps to Prisma BankConnection table."""

    __tablename__ = "BankConnection"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    clientSetupId: Mapped[str] = mapped_column(
        String(30), ForeignKey("ClientSetup.id", ondelete="CASCADE"), nullable=False
    )
    plaidAccessToken: Mapped[str] = mapped_column(String(255), nullable=False)
    plaidItemId: Mapped[str] = mapped_column(String(100), nullable=False)
    accountId: Mapped[str] = mapped_column(String(100), nullable=False)
    accountName: Mapped[str] = mapped_column(String(255), nullable=False)
    accountMask: Mapped[str | None] = mapped_column(String(10), nullable=True)
    accountType: Mapped[str] = mapped_column(String(50), nullable=False)
    accountSubtype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    institutionName: Mapped[str] = mapped_column(String(255), nullable=False)
    institutionId: Mapped[str] = mapped_column(String(100), nullable=False)
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    clientSetup: Mapped["ClientSetup"] = relationship("ClientSetup", back_populates="bankConnections")

    def __repr__(self) -> str:
        return f"<BankConnection(id={self.id}, institutionName='{self.institutionName}')>"


def generate_cuid() -> str:
    """Generate a cuid-like ID for compatibility with Prisma."""
    import secrets
    import time

    # Simple cuid-like generator: timestamp + random
    timestamp = hex(int(time.time() * 1000))[2:]
    random_part = secrets.token_hex(8)
    return f"c{timestamp}{random_part}"[:25]
