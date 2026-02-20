"""TaxProfile model — tax calculation results per client.

Adapted from Helio's TaxProfile (helio/apps/api/app/db/models.py).
Changes from Helio original:
  - client_id is Integer FK to Nova's clients.id (was String in Helio)
  - Uses Nova's Base + TimestampMixin instead of manual timestamps
  - Table name kept as 'tax_profiles' (no conflict with Nova)
"""

from uuid import uuid4

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.shared.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid4())


class TaxProfile(Base, TimestampMixin):
    """Tax calculation results and cached summary for a client in a given tax year."""

    __tablename__ = "tax_profiles"
    __table_args__ = (UniqueConstraint("client_id", "tax_year"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    tax_year: Mapped[str] = mapped_column(String, nullable=False)

    # Cached summary
    total_income: Mapped[float] = mapped_column(Float, default=0.0)
    adjusted_net_income: Mapped[float] = mapped_column(Float, default=0.0)
    taxable_income: Mapped[float] = mapped_column(Float, default=0.0)
    income_tax: Mapped[float] = mapped_column(Float, default=0.0)
    national_insurance: Mapped[float] = mapped_column(Float, default=0.0)
    dividend_tax: Mapped[float] = mapped_column(Float, default=0.0)
    total_tax: Mapped[float] = mapped_column(Float, default=0.0)
    effective_rate: Mapped[float] = mapped_column(Float, default=0.0)
    marginal_rate: Mapped[float] = mapped_column(Float, default=0.0)
    personal_allowance: Mapped[float] = mapped_column(Float, default=12570.0)
    pa_status: Mapped[str] = mapped_column(String, default="full")

    # Flags
    in_pa_taper_zone: Mapped[bool] = mapped_column(Boolean, default=False)
    hicbc_applies: Mapped[bool] = mapped_column(Boolean, default=False)
    pension_taper_applies: Mapped[bool] = mapped_column(Boolean, default=False)

    # JSONB expansion joints
    tax_breakdown: Mapped[list | None] = mapped_column(JSON, default=list)
    ni_breakdown: Mapped[dict | None] = mapped_column(JSON, default=dict)
    income_sources: Mapped[list | None] = mapped_column(JSON, default=list)
    pension_data: Mapped[dict | None] = mapped_column(JSON, default=dict)
    allowances: Mapped[list | None] = mapped_column(JSON, default=list)
    hicbc: Mapped[dict | None] = mapped_column(JSON, default=dict)
    scenarios: Mapped[list | None] = mapped_column(JSON, default=list)

    # Meta
    status: Mapped[str] = mapped_column(String, default="draft")
    data_confidence: Mapped[str] = mapped_column(String, default="low")
    confidence_notes: Mapped[list | None] = mapped_column(JSON, default=list)
    source_notes: Mapped[list | None] = mapped_column(JSON, default=list)

    def __repr__(self) -> str:
        return f"<TaxProfile(id={self.id}, client_id={self.client_id}, tax_year='{self.tax_year}')>"
