"""Service layer for Request Set and Request Item operations."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.request_set import RequestSet
from app.models.request_item import RequestItem
from app.schemas.request import (
    RequestSetCreate,
    RequestSetUpdate,
    RequestItemCreate,
    RequestItemUpdate,
)


class RequestSetService:
    """Service for managing request sets."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: RequestSetCreate) -> RequestSet:
        """Create a new request set."""
        request_set = RequestSet(**data.model_dump())
        self.db.add(request_set)
        self.db.commit()
        self.db.refresh(request_set)
        return request_set

    def get(self, request_set_id: int) -> RequestSet | None:
        """Get a request set by ID."""
        return self.db.get(RequestSet, request_set_id)

    def list_by_engagement(
        self, engagement_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[RequestSet], int]:
        """List request sets for an engagement."""
        stmt = (
            select(RequestSet)
            .where(RequestSet.engagement_id == engagement_id)
            .order_by(RequestSet.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        request_sets = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(func.count(RequestSet.id))
            .filter(RequestSet.engagement_id == engagement_id)
            .scalar()
        )
        return request_sets, total or 0

    def update(self, request_set_id: int, data: RequestSetUpdate) -> RequestSet | None:
        """Update a request set."""
        request_set = self.get(request_set_id)
        if not request_set:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(request_set, field, value)

        self.db.commit()
        self.db.refresh(request_set)
        return request_set

    def delete(self, request_set_id: int) -> bool:
        """Delete a request set."""
        request_set = self.get(request_set_id)
        if not request_set:
            return False

        self.db.delete(request_set)
        self.db.commit()
        return True


class RequestItemService:
    """Service for managing request items."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: RequestItemCreate) -> RequestItem:
        """Create a new request item."""
        request_item = RequestItem(**data.model_dump())
        self.db.add(request_item)
        self.db.commit()
        self.db.refresh(request_item)
        return request_item

    def get(self, request_item_id: int) -> RequestItem | None:
        """Get a request item by ID."""
        return self.db.get(RequestItem, request_item_id)

    def list_by_request_set(
        self, request_set_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[RequestItem], int]:
        """List request items for a request set."""
        stmt = (
            select(RequestItem)
            .where(RequestItem.request_set_id == request_set_id)
            .order_by(RequestItem.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        request_items = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(func.count(RequestItem.id))
            .filter(RequestItem.request_set_id == request_set_id)
            .scalar()
        )
        return request_items, total or 0

    def update(self, request_item_id: int, data: RequestItemUpdate) -> RequestItem | None:
        """Update a request item."""
        request_item = self.get(request_item_id)
        if not request_item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(request_item, field, value)

        self.db.commit()
        self.db.refresh(request_item)
        return request_item

    def delete(self, request_item_id: int) -> bool:
        """Delete a request item."""
        request_item = self.get(request_item_id)
        if not request_item:
            return False

        self.db.delete(request_item)
        self.db.commit()
        return True

    def link_document(self, request_item_id: int, document_id: int) -> bool:
        """Link a document to a request item."""
        from app.models.document import Document
        
        request_item = self.get(request_item_id)
        document = self.db.get(Document, document_id)
        
        if not request_item or not document:
            return False
        
        if document not in request_item.documents:
            request_item.documents.append(document)
            self.db.commit()
        
        return True

    def unlink_document(self, request_item_id: int, document_id: int) -> bool:
        """Unlink a document from a request item."""
        from app.models.document import Document
        
        request_item = self.get(request_item_id)
        document = self.db.get(Document, document_id)
        
        if not request_item or not document:
            return False
        
        if document in request_item.documents:
            request_item.documents.remove(document)
            self.db.commit()
        
        return True
