"""API routes for Document management."""

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.document import (
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
    ExtractedData,
    PresignedUrlResponse,
)
from app.services.document_service import DocumentService
from app.services.evidence_service import EvidenceService
from app.tasks.document_tasks import run_process_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    evidence_item_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auto_process: bool = True,
) -> DocumentUploadResponse:
    """Upload a document for an evidence item.

    Args:
        evidence_item_id: ID of the evidence item to attach the document to
        file: The file to upload
        auto_process: If True, automatically queue the document for AI processing
    """
    evidence_service = EvidenceService(db)
    if not evidence_service.get(evidence_item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence item not found"
        )

    service = DocumentService(db)
    try:
        doc, is_duplicate = service.upload(
            file=file.file,
            filename=file.filename or "unnamed",
            evidence_item_id=evidence_item_id,
            content_type=file.content_type or "application/octet-stream",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

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
    evidence_item_id: int | None = None,
    vat_period_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> DocumentList:
    """List documents, optionally filtered by evidence item or VAT period."""
    service = DocumentService(db)

    if evidence_item_id:
        docs, total = service.list_by_evidence_item(
            evidence_item_id, skip=skip, limit=limit
        )
    elif vat_period_id:
        docs, total = service.list_by_period(vat_period_id, skip=skip, limit=limit)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either evidence_item_id or vat_period_id is required",
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
        raw_data=doc.extracted_data,
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
    from app.models.document import DocumentStatus

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
