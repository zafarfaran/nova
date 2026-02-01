"""API routes for Request Sets and Request Items."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.request import (
    RequestSetCreate,
    RequestSetList,
    RequestSetResponse,
    RequestSetUpdate,
    RequestItemCreate,
    RequestItemList,
    RequestItemResponse,
    RequestItemUpdate,
)
from app.services.engagement_service import EngagementService
from app.services.request_service import RequestSetService, RequestItemService

router = APIRouter(prefix="/requests", tags=["requests"])


# Request Set endpoints
@router.post("/sets", response_model=RequestSetResponse, status_code=status.HTTP_201_CREATED)
def create_request_set(
    data: RequestSetCreate, db: Session = Depends(get_db)
) -> RequestSetResponse:
    """Create a new request set."""
    engagement_service = EngagementService(db)
    if not engagement_service.get(data.engagement_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    service = RequestSetService(db)
    request_set = service.create(data)
    return RequestSetResponse.model_validate(request_set)


@router.get("/sets", response_model=RequestSetList)
def list_request_sets(
    engagement_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> RequestSetList:
    """List request sets for an engagement."""
    engagement_service = EngagementService(db)
    if not engagement_service.get(engagement_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    service = RequestSetService(db)
    request_sets, total = service.list_by_engagement(engagement_id, skip=skip, limit=limit)
    return RequestSetList(
        items=[RequestSetResponse.model_validate(rs) for rs in request_sets], total=total
    )


@router.get("/sets/{request_set_id}", response_model=RequestSetResponse)
def get_request_set(
    request_set_id: int, db: Session = Depends(get_db)
) -> RequestSetResponse:
    """Get a request set by ID."""
    service = RequestSetService(db)
    request_set = service.get(request_set_id)
    if not request_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request set not found"
        )
    return RequestSetResponse.model_validate(request_set)


@router.patch("/sets/{request_set_id}", response_model=RequestSetResponse)
def update_request_set(
    request_set_id: int, data: RequestSetUpdate, db: Session = Depends(get_db)
) -> RequestSetResponse:
    """Update a request set."""
    service = RequestSetService(db)
    request_set = service.update(request_set_id, data)
    if not request_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request set not found"
        )
    return RequestSetResponse.model_validate(request_set)


@router.delete("/sets/{request_set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request_set(request_set_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a request set."""
    service = RequestSetService(db)
    if not service.delete(request_set_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request set not found"
        )


# Request Item endpoints
@router.post("/items", response_model=RequestItemResponse, status_code=status.HTTP_201_CREATED)
def create_request_item(
    data: RequestItemCreate, db: Session = Depends(get_db)
) -> RequestItemResponse:
    """Create a new request item."""
    set_service = RequestSetService(db)
    if not set_service.get(data.request_set_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request set not found"
        )

    service = RequestItemService(db)
    request_item = service.create(data)
    return RequestItemResponse.model_validate(request_item)


@router.get("/items", response_model=RequestItemList)
def list_request_items(
    request_set_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> RequestItemList:
    """List request items for a request set."""
    set_service = RequestSetService(db)
    if not set_service.get(request_set_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request set not found"
        )

    service = RequestItemService(db)
    request_items, total = service.list_by_request_set(request_set_id, skip=skip, limit=limit)
    return RequestItemList(
        items=[RequestItemResponse.model_validate(ri) for ri in request_items], total=total
    )


@router.get("/items/{request_item_id}", response_model=RequestItemResponse)
def get_request_item(
    request_item_id: int, db: Session = Depends(get_db)
) -> RequestItemResponse:
    """Get a request item by ID."""
    service = RequestItemService(db)
    request_item = service.get(request_item_id)
    if not request_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request item not found"
        )
    return RequestItemResponse.model_validate(request_item)


@router.patch("/items/{request_item_id}", response_model=RequestItemResponse)
def update_request_item(
    request_item_id: int, data: RequestItemUpdate, db: Session = Depends(get_db)
) -> RequestItemResponse:
    """Update a request item."""
    service = RequestItemService(db)
    request_item = service.update(request_item_id, data)
    if not request_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request item not found"
        )
    return RequestItemResponse.model_validate(request_item)


@router.delete("/items/{request_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request_item(request_item_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a request item."""
    service = RequestItemService(db)
    if not service.delete(request_item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request item not found"
        )


@router.post("/items/{request_item_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def link_document_to_request_item(
    request_item_id: int, document_id: int, db: Session = Depends(get_db)
) -> None:
    """Link a document to a request item."""
    service = RequestItemService(db)
    if not service.link_document(request_item_id, document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request item or document not found",
        )


@router.delete("/items/{request_item_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_document_from_request_item(
    request_item_id: int, document_id: int, db: Session = Depends(get_db)
) -> None:
    """Unlink a document from a request item."""
    service = RequestItemService(db)
    if not service.unlink_document(request_item_id, document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request item or document not found",
        )
