"""Pydantic schemas for Evidence."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.evidence import EvidenceCategory, EvidenceStatus


class EvidenceItemBase(BaseModel):
    """Base schema for Evidence Item."""

    vat_period_id: int
    category: EvidenceCategory
    description: str | None = None
    expected_count: int = 0
    notes: str | None = None


class EvidenceItemCreate(EvidenceItemBase):
    """Schema for creating an Evidence Item."""

    pass


class EvidenceItemUpdate(BaseModel):
    """Schema for updating an Evidence Item."""

    description: str | None = None
    status: EvidenceStatus | None = None
    expected_count: int | None = None
    received_count: int | None = None
    notes: str | None = None


class EvidenceItemResponse(EvidenceItemBase):
    """Schema for Evidence Item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: EvidenceStatus
    received_count: int
    coverage_percentage: float
    is_complete: bool
    created_at: datetime
    updated_at: datetime


class EvidenceItemList(BaseModel):
    """Schema for listing evidence items."""

    items: list[EvidenceItemResponse]
    total: int


class CoverageMetric(BaseModel):
    """Coverage metric for a single evidence category."""

    category: EvidenceCategory
    expected_count: int
    received_count: int
    coverage_percentage: float
    status: EvidenceStatus


class CoverageSummary(BaseModel):
    """Summary of coverage for a VAT period."""

    vat_period_id: int
    total_expected: int
    total_received: int
    overall_coverage_percentage: float
    categories: list[CoverageMetric]
    is_complete: bool


class GapItem(BaseModel):
    """A gap in evidence collection."""

    evidence_item_id: int
    category: EvidenceCategory
    description: str | None
    expected_count: int
    received_count: int
    missing_count: int
    coverage_percentage: float


class GapReport(BaseModel):
    """Report of all gaps in evidence for a VAT period."""

    vat_period_id: int
    gaps: list[GapItem]
    total_missing: int
