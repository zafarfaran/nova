"""API routes for Audit Log."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.engagements import Engagement
from app.models.clients import Client
from app.schemas.audit import AuditLogResponse, AuditLogList
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/engagement/{engagement_id}", response_model=AuditLogList)
def get_audit_by_engagement(
    engagement_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> AuditLogList:
    """Get audit logs for an engagement."""
    engagement = db.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    service = AuditService(db)
    entries, total = service.get_by_engagement(engagement_id, skip=skip, limit=limit)
    return AuditLogList(
        items=[AuditLogResponse.model_validate(e) for e in entries], total=total
    )


@router.get("/client/{client_id}", response_model=AuditLogList)
def get_audit_by_client(
    client_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> AuditLogList:
    """Get audit logs for a client."""
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    service = AuditService(db)
    entries, total = service.get_by_client(client_id, skip=skip, limit=limit)
    return AuditLogList(
        items=[AuditLogResponse.model_validate(e) for e in entries], total=total
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=AuditLogList)
def get_audit_by_entity(
    entity_type: str,
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> AuditLogList:
    """Get audit logs for a specific entity."""
    service = AuditService(db)
    entries, total = service.get_by_entity(entity_type, entity_id, skip=skip, limit=limit)
    return AuditLogList(
        items=[AuditLogResponse.model_validate(e) for e in entries], total=total
    )
