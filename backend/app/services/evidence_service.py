"""Service layer for Evidence operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.vat_rules import DEFAULT_EVIDENCE_REQUIREMENTS
from app.models.evidence import EvidenceCategory, EvidenceItem, EvidenceStatus
from app.models.vat_period import VATPeriod
from app.schemas.evidence import (
    CoverageMetric,
    CoverageSummary,
    EvidenceItemCreate,
    EvidenceItemUpdate,
    GapItem,
    GapReport,
)


class EvidenceService:
    """Service for managing evidence items."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: EvidenceItemCreate) -> EvidenceItem:
        """Create a new evidence item."""
        item = EvidenceItem(**data.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get(self, item_id: int) -> EvidenceItem | None:
        """Get an evidence item by ID."""
        return self.db.get(EvidenceItem, item_id)

    def list_by_period(
        self, period_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[EvidenceItem], int]:
        """List all evidence items for a VAT period."""
        stmt = (
            select(EvidenceItem)
            .where(EvidenceItem.vat_period_id == period_id)
            .offset(skip)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(EvidenceItem)
            .filter(EvidenceItem.vat_period_id == period_id)
            .count()
        )
        return items, total

    def update(self, item_id: int, data: EvidenceItemUpdate) -> EvidenceItem | None:
        """Update an evidence item."""
        item = self.get(item_id)
        if not item:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        # Auto-update status based on counts
        if item.received_count >= item.expected_count and item.expected_count > 0:
            item.status = EvidenceStatus.COMPLETE
        elif item.received_count > 0:
            item.status = EvidenceStatus.PARTIAL

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        """Delete an evidence item."""
        item = self.get(item_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    def build_schedule(
        self, period_id: int, include_optional: bool = False
    ) -> list[EvidenceItem]:
        """Build evidence schedule for a VAT period based on standard requirements."""
        period = self.db.get(VATPeriod, period_id)
        if not period:
            raise ValueError(f"VAT period {period_id} not found")

        # Check if schedule already exists
        existing = (
            self.db.query(EvidenceItem)
            .filter(EvidenceItem.vat_period_id == period_id)
            .count()
        )
        if existing > 0:
            raise ValueError(
                f"Evidence schedule already exists for period {period_id}"
            )

        created_items = []
        for category_name, config in DEFAULT_EVIDENCE_REQUIREMENTS.items():
            if not include_optional and not config.get("required", False):
                continue

            category = EvidenceCategory(category_name)
            item = EvidenceItem(
                vat_period_id=period_id,
                category=category,
                description=config.get("description"),
                status=EvidenceStatus.PENDING,
                expected_count=0,  # Will be set manually or via chaser
                received_count=0,
            )
            self.db.add(item)
            created_items.append(item)

        self.db.commit()
        for item in created_items:
            self.db.refresh(item)

        return created_items

    def get_coverage(self, period_id: int) -> CoverageSummary:
        """Calculate coverage metrics for a VAT period."""
        items, _ = self.list_by_period(period_id, limit=1000)

        if not items:
            return CoverageSummary(
                vat_period_id=period_id,
                total_expected=0,
                total_received=0,
                overall_coverage_percentage=0.0,
                categories=[],
                is_complete=False,
            )

        total_expected = sum(item.expected_count for item in items)
        total_received = sum(item.received_count for item in items)

        overall_coverage = (
            (total_received / total_expected * 100) if total_expected > 0 else 0.0
        )

        categories = [
            CoverageMetric(
                category=item.category,
                expected_count=item.expected_count,
                received_count=item.received_count,
                coverage_percentage=item.coverage_percentage,
                status=item.status,
            )
            for item in items
        ]

        is_complete = all(item.is_complete for item in items if item.expected_count > 0)

        return CoverageSummary(
            vat_period_id=period_id,
            total_expected=total_expected,
            total_received=total_received,
            overall_coverage_percentage=overall_coverage,
            categories=categories,
            is_complete=is_complete,
        )

    def get_gaps(self, period_id: int) -> GapReport:
        """Get gaps report for a VAT period."""
        items, _ = self.list_by_period(period_id, limit=1000)

        gaps = []
        total_missing = 0

        for item in items:
            if item.expected_count > 0 and item.received_count < item.expected_count:
                missing = item.expected_count - item.received_count
                total_missing += missing
                gaps.append(
                    GapItem(
                        evidence_item_id=item.id,
                        category=item.category,
                        description=item.description,
                        expected_count=item.expected_count,
                        received_count=item.received_count,
                        missing_count=missing,
                        coverage_percentage=item.coverage_percentage,
                    )
                )

        return GapReport(
            vat_period_id=period_id,
            gaps=gaps,
            total_missing=total_missing,
        )

    def increment_received(self, item_id: int, count: int = 1) -> EvidenceItem | None:
        """Increment the received count for an evidence item."""
        item = self.get(item_id)
        if not item:
            return None

        item.received_count += count

        # Auto-update status
        if item.received_count >= item.expected_count and item.expected_count > 0:
            item.status = EvidenceStatus.COMPLETE
        elif item.received_count > 0:
            item.status = EvidenceStatus.PARTIAL

        self.db.commit()
        self.db.refresh(item)
        return item
