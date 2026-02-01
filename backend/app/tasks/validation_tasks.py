"""Background tasks for document validation."""

import logging

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.engagement import Engagement
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


def validate_engagement_documents(engagement_id: int) -> int:
    """Validate all extracted documents in an engagement.

    Returns the number of documents validated.
    """
    db = SessionLocal()
    try:
        # Get all extracted documents for the engagement
        stmt = (
            select(Document)
            .where(
                Document.engagement_id == engagement_id,
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

    Runs specialized AI validation on all documents across all engagements.
    Uses document-specific AI agents (Invoice, Bank Statement, Receipt, etc.)
    for better accuracy.

    Args:
        client_id: ID of the client

    Returns:
        dict with validation statistics
    """
    db = SessionLocal()
    try:
        # Get all extracted documents for all engagements belonging to this client
        stmt = (
            select(Document)
            .where(
                Document.client_id == client_id,
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
                    f"Validating document {doc.id} ({doc.filename})"
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


# Keep old function name for backwards compatibility
def validate_period_documents(period_id: int) -> int:
    """Alias for validate_engagement_documents for backwards compatibility."""
    return validate_engagement_documents(period_id)
