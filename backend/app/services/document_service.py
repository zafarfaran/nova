"""Service layer for Document operations."""

from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.evidence import EvidenceItem
from app.models.vat_period import VATPeriod
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.evidence_service import EvidenceService
from app.storage import StorageProvider, get_storage
from app.utils.hashing import compute_file_hash


class DocumentService:
    """Service for managing documents."""

    def __init__(self, db: Session, storage: StorageProvider | None = None):
        self.db = db
        self.storage = storage or get_storage()

    def create(self, data: DocumentCreate) -> Document:
        """Create a new document record."""
        doc = Document(**data.model_dump())
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get(self, doc_id: int) -> Document | None:
        """Get a document by ID."""
        return self.db.get(Document, doc_id)

    def get_by_hash(self, file_hash: str) -> Document | None:
        """Get a document by file hash."""
        stmt = select(Document).where(Document.file_hash == file_hash)
        return self.db.scalars(stmt).first()

    def list_by_evidence_item(
        self, evidence_item_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[Document], int]:
        """List all documents for an evidence item."""
        stmt = (
            select(Document)
            .where(Document.evidence_item_id == evidence_item_id)
            .offset(skip)
            .limit(limit)
        )
        docs = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(Document)
            .filter(Document.evidence_item_id == evidence_item_id)
            .count()
        )
        return docs, total

    def list_by_period(
        self, period_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[Document], int]:
        """List all documents for a VAT period."""
        stmt = (
            select(Document)
            .join(EvidenceItem)
            .where(EvidenceItem.vat_period_id == period_id)
            .offset(skip)
            .limit(limit)
        )
        docs = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(Document)
            .join(EvidenceItem)
            .filter(EvidenceItem.vat_period_id == period_id)
            .count()
        )
        return docs, total

    def update(self, doc_id: int, data: DocumentUpdate) -> Document | None:
        """Update a document."""
        doc = self.get(doc_id)
        if not doc:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(doc, key, value)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def delete(self, doc_id: int) -> bool:
        """Delete a document and its S3 file."""
        doc = self.get(doc_id)
        if not doc:
            return False

        # Delete from S3
        try:
            self.storage.delete_file(doc.s3_key)
        except Exception:
            pass  # Continue even if S3 deletion fails

        self.db.delete(doc)
        self.db.commit()
        return True

    def upload(
        self,
        file: BinaryIO,
        filename: str,
        evidence_item_id: int,
        content_type: str = "application/octet-stream",
    ) -> tuple[Document, bool]:
        """Upload a document and create a record.

        Returns:
            Tuple of (Document, is_duplicate)
        """
        # Get evidence item to find client and period
        evidence_item = self.db.get(EvidenceItem, evidence_item_id)
        if not evidence_item:
            raise ValueError(f"Evidence item {evidence_item_id} not found")

        period = self.db.get(VATPeriod, evidence_item.vat_period_id)
        if not period:
            raise ValueError("VAT period not found")

        # Compute file hash for duplicate detection
        file_hash = compute_file_hash(file)

        # Check for duplicates
        existing = self.get_by_hash(file_hash)
        if existing:
            return existing, True

        # Get file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        # Upload to S3
        s3_key = self.storage.upload_file(
            file=file,
            filename=filename,
            client_id=period.client_id,
            period_id=period.id,
            content_type=content_type,
        )

        # Create document record
        doc_data = DocumentCreate(
            evidence_item_id=evidence_item_id,
            filename=filename,
            s3_key=s3_key,
            file_hash=file_hash,
            content_type=content_type,
            file_size=file_size,
        )
        doc = self.create(doc_data)

        # Increment evidence item received count
        evidence_service = EvidenceService(self.db)
        evidence_service.increment_received(evidence_item_id)

        return doc, False

    def get_download_url(self, doc_id: int, expiration: int = 3600) -> str:
        """Get a presigned URL for downloading a document."""
        doc = self.get(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")
        return self.storage.get_presigned_url(doc.s3_key, expiration=expiration)

    def download(self, doc_id: int) -> tuple[bytes, str, str]:
        """Download a document.

        Returns:
            Tuple of (content, filename, content_type)
        """
        doc = self.get(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        content = self.storage.download_file(doc.s3_key)
        return content, doc.filename, doc.content_type or "application/octet-stream"

    def update_status(
        self, doc_id: int, status: DocumentStatus, error: str | None = None
    ) -> Document | None:
        """Update document processing status."""
        doc = self.get(doc_id)
        if not doc:
            return None
        doc.status = status
        if error:
            doc.processing_error = error
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def update_extracted_data(
        self, doc_id: int, extracted_data: dict
    ) -> Document | None:
        """Update document with extracted data."""
        doc = self.get(doc_id)
        if not doc:
            return None

        doc.extracted_data = extracted_data
        doc.status = DocumentStatus.EXTRACTED

        # Update key fields
        doc.invoice_number = extracted_data.get("invoice_number")
        doc.invoice_date = extracted_data.get("invoice_date")
        doc.supplier_name = extracted_data.get("supplier_name")
        doc.supplier_vat_number = extracted_data.get("supplier_vat_number")
        doc.customer_name = extracted_data.get("customer_name")
        doc.customer_vat_number = extracted_data.get("customer_vat_number")
        doc.net_amount = extracted_data.get("net_amount")
        doc.vat_amount = extracted_data.get("vat_amount")
        doc.gross_amount = extracted_data.get("gross_amount")
        doc.vat_rate = extracted_data.get("vat_rate")
        doc.currency = extracted_data.get("currency", "GBP")
        doc.description = extracted_data.get("description")

        self.db.commit()
        self.db.refresh(doc)
        return doc
