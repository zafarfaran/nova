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


def validate_client_documents(client_id: int) -> dict:
    """Validate all extracted documents for a client.

    Runs specialized AI validation on all documents across all VAT periods.
    Uses document-specific AI agents (Invoice, Bank Statement, Receipt, etc.)
    for better accuracy.

    Args:
        client_id: ID of the client

    Returns:
        dict with validation statistics
    """
    from app.models.vat_period import VATPeriod

    db = SessionLocal()
    try:
        # Get all extracted documents for all periods belonging to this client
        stmt = (
            select(Document)
            .join(EvidenceItem)
            .join(VATPeriod)
            .where(
                VATPeriod.client_id == client_id,
                Document.status.in_([DocumentStatus.EXTRACTED, DocumentStatus.VALIDATED]),
            )
        )
        documents = list(db.scalars(stmt).all())

        logger.info(
            f"Starting validation for client {client_id}: found {len(documents)} documents"
        )

        service = ValidationService(db)
        validated_count = 0
        failed_count = 0
        total_issues = 0

        for doc in documents:
            try:
                logger.info(
                    f"Validating document {doc.id} ({doc.filename}) "
                    f"- type: {doc.document_type}"
                )
                results = service.validate_document(doc.id, include_ai_validation=True)

                validated_count += 1
                issues = len([r for r in results if r.status.value in ['failed', 'warning']])
                total_issues += issues

                logger.info(
                    f"Document {doc.id} validation complete: {issues} issues found"
                )
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to validate document {doc.id}: {e}")

        summary = {
            "client_id": client_id,
            "total_documents": len(documents),
            "validated": validated_count,
            "failed_to_validate": failed_count,
            "total_issues_found": total_issues,
        }

        logger.info(f"Client {client_id} validation complete: {summary}")

        return summary
    finally:
        db.close()
