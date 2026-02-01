"""API routes for Document management."""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.documents import Document, DocumentStatus
from app.models.engagements import Engagement
from app.models.requests import RequestSet, RequestItem
from app.schemas.document import (
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
    ExtractedData,
    PresignedUrlResponse,
)
from app.services.documents import DocumentService
from app.tasks.documents import run_process_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


# Schema for sync request
class DocumentSyncRequest(BaseModel):
    """Request to sync a document from external storage (e.g., UploadThing)."""
    filename: str
    external_url: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    client_id: int
    engagement_id: Optional[int] = None
    request_item_id: Optional[int] = None


class DocumentSyncResponse(BaseModel):
    """Response from document sync."""
    success: bool
    document_id: Optional[int] = None
    message: str


class BatchProcessRequest(BaseModel):
    """Request to process multiple documents."""
    document_ids: Optional[list[int]] = None
    force: bool = False


class BatchProcessResponse(BaseModel):
    """Response from batch processing."""
    success: bool
    queued_count: int
    message: str


class ReprocessStuckRequest(BaseModel):
    """Request to reprocess stuck documents."""

    older_than_minutes: int = 30
    requeue: bool = True


class ReprocessStuckResponse(BaseModel):
    """Response for reprocessing stuck documents."""

    success: bool
    stuck_count: int
    requeued_count: int
    failed_count: int
    document_ids: list[int]


@router.post("/sync", response_model=DocumentSyncResponse)
async def sync_document(
    request: DocumentSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> DocumentSyncResponse:
    """Sync a document from external storage (UploadThing) to backend.

    This endpoint:
    1. Creates a document record with the external URL as s3_key
    2. Queues the document for AI extraction
    """
    logger.info(f"Syncing document: {request.filename} for client {request.client_id}")

    # Extract file key from URL (UploadThing URLs are like https://utfs.io/f/{key})
    s3_key = request.external_url
    if "utfs.io/f/" in request.external_url:
        s3_key = request.external_url.split("utfs.io/f/")[-1]

    # Check for duplicate by URL
    stmt = select(Document).where(Document.s3_key == s3_key)
    existing = db.scalars(stmt).first()
    if existing:
        logger.info(f"Document already exists: {existing.id}")
        return DocumentSyncResponse(
            success=True,
            document_id=existing.id,
            message="Document already synced"
        )

    # Create file hash from URL (since we don't have the actual file content)
    file_hash = hashlib.sha256(request.external_url.encode()).hexdigest()

    # Create document record
    doc = Document(
        client_id=request.client_id,
        engagement_id=request.engagement_id,
        filename=request.filename,
        s3_key=s3_key,
        file_hash=file_hash,
        content_type=request.content_type or "application/pdf",
        file_size=request.file_size,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    logger.info(f"Created document {doc.id} for {request.filename}")

    # Link to request item if provided
    if request.request_item_id:
        request_item = db.get(RequestItem, request.request_item_id)
        if request_item and doc not in request_item.documents:
            request_item.documents.append(doc)
            db.commit()

    # Queue for AI extraction
    background_tasks.add_task(run_process_document, doc.id)
    logger.info(f"Queued document {doc.id} for extraction")

    return DocumentSyncResponse(
        success=True,
        document_id=doc.id,
        message="Document synced and queued for extraction"
    )


@router.post("/process-all/{engagement_id}", response_model=BatchProcessResponse)
async def process_all_documents(
    engagement_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    force: bool = False,
) -> BatchProcessResponse:
    """Process all pending documents for an engagement.

    This triggers AI extraction for all documents that haven't been processed yet.
    """
    logger.info(f"Processing all documents for engagement {engagement_id}")

    # Verify engagement exists
    engagement = db.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    # Get all documents for this engagement that need processing
    stmt = select(Document).where(Document.engagement_id == engagement_id)

    if not force:
        stmt = stmt.where(Document.status == DocumentStatus.PENDING)

    docs = list(db.scalars(stmt).all())

    if not docs:
        return BatchProcessResponse(
            success=True,
            queued_count=0,
            message="No documents to process"
        )

    # Queue each document for processing
    for doc in docs:
        doc.status = DocumentStatus.PROCESSING
        background_tasks.add_task(run_process_document, doc.id)

    db.commit()
    logger.info(f"Queued {len(docs)} documents for processing")

    return BatchProcessResponse(
        success=True,
        queued_count=len(docs),
        message=f"Queued {len(docs)} document(s) for extraction"
    )


@router.post("/reprocess-stuck", response_model=ReprocessStuckResponse)
async def reprocess_stuck_documents(
    request: ReprocessStuckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ReprocessStuckResponse:
    """Reprocess documents stuck in PROCESSING beyond a threshold."""
    cutoff = datetime.utcnow() - timedelta(minutes=request.older_than_minutes)
    stmt = select(Document).where(
        Document.status == DocumentStatus.PROCESSING,
        Document.updated_at < cutoff,
    )
    stuck_docs = list(db.scalars(stmt).all())

    for doc in stuck_docs:
        doc.processing_error = (
            f"Processing stuck for > {request.older_than_minutes} minutes"
        )
        doc.status = (
            DocumentStatus.PENDING if request.requeue else DocumentStatus.FAILED
        )

    db.commit()

    if request.requeue:
        for doc in stuck_docs:
            background_tasks.add_task(run_process_document, doc.id)

    return ReprocessStuckResponse(
        success=True,
        stuck_count=len(stuck_docs),
        requeued_count=len(stuck_docs) if request.requeue else 0,
        failed_count=len(stuck_docs) if not request.requeue else 0,
        document_ids=[doc.id for doc in stuck_docs],
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    client_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    engagement_id: int | None = None,
    request_item_id: int | None = None,
    auto_process: bool = True,
) -> DocumentUploadResponse:
    """Upload a document for a client.

    Args:
        client_id: ID of the client
        file: The file to upload
        engagement_id: Optional ID of the engagement
        request_item_id: Optional ID of the request item to link
        auto_process: If True, automatically queue the document for AI processing
    """
    service = DocumentService(db)
    try:
        doc, is_duplicate = service.upload(
            file=file.file,
            filename=file.filename or "unnamed",
            client_id=client_id,
            engagement_id=engagement_id,
            content_type=file.content_type or "application/octet-stream",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    # Link to request item if provided
    if request_item_id and not is_duplicate:
        request_item = db.get(RequestItem, request_item_id)
        if request_item and doc not in request_item.documents:
            request_item.documents.append(doc)
            db.commit()

    # Queue for AI processing if not a duplicate and auto_process is enabled
    if not is_duplicate and auto_process:
        background_tasks.add_task(run_process_document, doc.id)

    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
        is_duplicate=is_duplicate,
        duplicate_document_id=doc.id if is_duplicate else None,
    )


@router.get("", response_model=DocumentList)
def list_documents(
    client_id: int | None = None,
    engagement_id: int | None = None,
    request_item_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> DocumentList:
    """List documents, optionally filtered by client, engagement, or request item."""
    service = DocumentService(db)

    if request_item_id:
        docs, total = service.list_by_request_item(request_item_id, skip=skip, limit=limit)
    elif engagement_id:
        docs, total = service.list_by_engagement(engagement_id, skip=skip, limit=limit)
    elif client_id:
        docs, total = service.list_by_client(client_id, skip=skip, limit=limit)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either client_id, engagement_id, or request_item_id is required",
        )

    return DocumentList(
        items=[DocumentResponse.model_validate(d) for d in docs], total=total
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)) -> DocumentResponse:
    """Get a document by ID."""
    service = DocumentService(db)
    doc = service.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return DocumentResponse.model_validate(doc)


@router.patch("/{doc_id}", response_model=DocumentResponse)
def update_document(
    doc_id: int, data: DocumentUpdate, db: Session = Depends(get_db)
) -> DocumentResponse:
    """Update a document."""
    service = DocumentService(db)
    doc = service.update(doc_id, data)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return DocumentResponse.model_validate(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a document."""
    service = DocumentService(db)
    if not service.delete(doc_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )


@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)) -> Response:
    """Download a document."""
    service = DocumentService(db)
    try:
        content, filename, content_type = service.download(doc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found in storage"
        )

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{doc_id}/download-url", response_model=PresignedUrlResponse)
def get_download_url(
    doc_id: int, expiration: int = 3600, db: Session = Depends(get_db)
) -> PresignedUrlResponse:
    """Get a presigned URL for downloading a document."""
    service = DocumentService(db)
    try:
        url = service.get_download_url(doc_id, expiration=expiration)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return PresignedUrlResponse(url=url, expires_in=expiration)


@router.get("/{doc_id}/extracted-data", response_model=ExtractedData)
def get_extracted_data(doc_id: int, db: Session = Depends(get_db)) -> ExtractedData:
    """Get AI-extracted data for a document."""
    service = DocumentService(db)
    doc = service.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Get extracted data from latest version if available
    extracted = doc.get_extracted_data() or {}

    return ExtractedData(
        invoice_number=doc.invoice_number,
        invoice_date=doc.invoice_date,
        supplier_name=doc.supplier_name,
        supplier_vat_number=doc.supplier_vat_number,
        customer_name=doc.customer_name,
        customer_vat_number=doc.customer_vat_number,
        net_amount=doc.net_amount,
        vat_amount=doc.vat_amount,
        gross_amount=doc.gross_amount,
        vat_rate=doc.vat_rate,
        currency=doc.currency,
        description=doc.description,
        raw_data=extracted,
    )


@router.post("/{doc_id}/process", response_model=DocumentResponse)
def process_document_endpoint(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    force: bool = False,
) -> DocumentResponse:
    """Manually trigger AI processing for a document.

    Args:
        doc_id: ID of the document to process
        force: If True, re-process even if already extracted. Defaults to False.
    """
    service = DocumentService(db)
    doc = service.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Skip if already extracted unless forced
    if not force and doc.status in [DocumentStatus.EXTRACTED, DocumentStatus.VALIDATED]:
        return DocumentResponse.model_validate(doc)

    # Queue for processing
    background_tasks.add_task(run_process_document, doc_id)

    return DocumentResponse.model_validate(doc)
