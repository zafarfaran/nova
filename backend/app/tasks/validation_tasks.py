"""Background tasks for document validation."""

import logging

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.evidence import EvidenceItem
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


def validate_document(document_id: int) -> None:
    """Validate a single document.

    This task runs all validation rules on a document.
    """
    db = SessionLocal()
    try:
        service = ValidationService(db)
        results = service.validate_document(document_id)
        logger.info(
            f"Validated document {document_id}: "
            f"{len([r for r in results if r.status.value == 'passed'])} passed, "
            f"{len([r for r in results if r.status.value == 'failed'])} failed"
        )
    except Exception as e:
        logger.error(f"Failed to validate document {document_id}: {e}")
    finally:
        db.close()


def validate_period_documents(period_id: int) -> int:
    """Validate all extracted documents in a VAT period.

    Returns the number of documents validated.
    """
    db = SessionLocal()
    try:
        # Get all extracted documents for the period
        stmt = (
            select(Document)
            .join(EvidenceItem)
            .where(
                EvidenceItem.vat_period_id == period_id,
                Document.status == DocumentStatus.EXTRACTED,
            )
        )
        documents = list(db.scalars(stmt).all())

        service = ValidationService(db)
        for doc in documents:
            try:
                service.validate_document(doc.id)
            except Exception as e:
                logger.error(f"Failed to validate document {doc.id}: {e}")

        return len(documents)
    finally:
        db.close()
