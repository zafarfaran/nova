"""Background tasks for document processing."""

import asyncio
import logging

from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.storage.s3 import S3Storage

logger = logging.getLogger(__name__)


async def process_document(document_id: int) -> None:
    """Process a document: download, extract data, and update record.

    This task:
    1. Downloads the document from S3
    2. Sends it to the AI provider for extraction
    3. Updates the document record with extracted data
    """
    db = SessionLocal()
    try:
        # Get document
        doc = db.get(Document, document_id)
        if not doc:
            logger.error(f"Document {document_id} not found")
            return

        # Update status to processing
        doc.status = DocumentStatus.PROCESSING
        db.commit()

        # Download from S3
        s3 = S3Storage()
        try:
            content = s3.download_file(doc.s3_key)
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.processing_error = f"S3 download failed: {str(e)}"
            db.commit()
            logger.error(f"Failed to download document {document_id}: {e}")
            return

        # Extract data using AI
        ai_provider = get_ai_provider()
        try:
            extracted_data = await ai_provider.extract_document_data(
                document_content=content,
                content_type=doc.content_type or "application/octet-stream",
                filename=doc.filename,
            )
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.processing_error = f"AI extraction failed: {str(e)}"
            db.commit()
            logger.error(f"Failed to extract data from document {document_id}: {e}")
            return

        # Update document with extracted data
        doc.extracted_data = extracted_data
        doc.status = DocumentStatus.EXTRACTED

        # Update key fields
        if "error" not in extracted_data:
            doc.invoice_number = extracted_data.get("invoice_number")
            doc.supplier_name = extracted_data.get("supplier_name")
            doc.supplier_vat_number = extracted_data.get("supplier_vat_number")
            doc.customer_name = extracted_data.get("customer_name")
            doc.customer_vat_number = extracted_data.get("customer_vat_number")
            doc.currency = extracted_data.get("currency", "GBP")
            doc.description = extracted_data.get("description")

            # Parse date
            if invoice_date := extracted_data.get("invoice_date"):
                try:
                    from datetime import datetime

                    doc.invoice_date = datetime.strptime(invoice_date, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass

            # Parse amounts
            for field in ["net_amount", "vat_amount", "gross_amount", "vat_rate"]:
                if value := extracted_data.get(field):
                    try:
                        from decimal import Decimal

                        setattr(doc, field, Decimal(str(value)))
                    except (ValueError, TypeError):
                        pass

            # Set document type
            if doc_type := extracted_data.get("detected_document_type"):
                from app.models.document import DocumentType

                try:
                    doc.document_type = DocumentType(doc_type)
                except ValueError:
                    pass

        db.commit()
        logger.info(f"Successfully processed document {document_id}")

    except Exception as e:
        logger.error(f"Unexpected error processing document {document_id}: {e}")
        try:
            doc = db.get(Document, document_id)
            if doc:
                doc.status = DocumentStatus.FAILED
                doc.processing_error = f"Unexpected error: {str(e)}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def run_process_document(document_id: int) -> None:
    """Sync wrapper for process_document to use with BackgroundTasks."""
    asyncio.run(process_document(document_id))


async def reprocess_failed_documents() -> int:
    """Reprocess all failed documents.

    Returns the number of documents queued for reprocessing.
    """
    db = SessionLocal()
    try:
        from sqlalchemy import select

        stmt = select(Document).where(Document.status == DocumentStatus.FAILED)
        failed_docs = list(db.scalars(stmt).all())

        for doc in failed_docs:
            doc.status = DocumentStatus.PENDING
            doc.processing_error = None
        db.commit()

        # Process each document
        for doc in failed_docs:
            await process_document(doc.id)

        return len(failed_docs)
    finally:
        db.close()
