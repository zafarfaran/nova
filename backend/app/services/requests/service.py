"""Service layer for Request Set and Request Item operations."""

from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.requests.set import RequestSet, RequestSetStatus
from app.models.requests.item import RequestItem, RequestItemStatus
from app.models.requests.template import RequestTemplate, RequestTemplateItem
from app.schemas.requests.request import (
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

    def create_from_template(
        self,
        engagement_id: int,
        template_id: int,
        name_override: str | None = None
    ) -> RequestSet:
        """Create a RequestSet from a RequestTemplate.
        
        Args:
            engagement_id: ID of the engagement to create the request set for
            template_id: ID of the template to use
            name_override: Optional custom name (defaults to template name with period)
            
        Returns:
            Created RequestSet with all items from template
            
        Raises:
            ValueError: If engagement or template not found, or types don't match
        """
        from app.models.engagements.engagement import Engagement
        
        # Get engagement with client relationship
        from sqlalchemy.orm import joinedload
        engagement = self.db.query(Engagement).options(joinedload(Engagement.client)).filter(Engagement.id == engagement_id).first()
        if not engagement:
            raise ValueError(f"Engagement {engagement_id} not found")
        
        # Get template with items
        template = self.db.get(RequestTemplate, template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        if not template.is_active:
            raise ValueError(f"Template {template_id} is not active")
        
        # Validate client type and engagement type match
        client_type = engagement.client.client_type if engagement.client else None
        if template.client_type and template.client_type != client_type:
            raise ValueError(
                f"Template client_type '{template.client_type}' doesn't match "
                f"client type '{client_type}'"
            )
        
        if template.engagement_type and template.engagement_type != engagement.engagement_type.value:
            raise ValueError(
                f"Template engagement_type '{template.engagement_type}' doesn't match "
                f"engagement type '{engagement.engagement_type.value}'"
            )
        
        # Generate name
        if name_override:
            name = name_override
        else:
            period_start = engagement.period_start.strftime("%Y-%m-%d")
            period_end = engagement.period_end.strftime("%Y-%m-%d")
            name = f"{template.name} — VAT Period {period_start} to {period_end}"
        
        # Create request set
        request_set = RequestSet(
            engagement_id=engagement_id,
            name=name,
            status=RequestSetStatus.DRAFT,
        )
        self.db.add(request_set)
        self.db.flush()
        
        # Create request items from template items (ordered by order_index)
        template_items = sorted(template.items, key=lambda x: x.order_index)
        
        for template_item in template_items:
            # Replace placeholders in description
            description = template_item.description or ""
            description = description.replace("[Q_START]", engagement.period_start.strftime("%Y-%m-%d"))
            description = description.replace("[Q_END]", engagement.period_end.strftime("%Y-%m-%d"))
            
            request_item = RequestItem(
                request_set_id=request_set.id,
                document_type_id=template_item.document_type_id,
                description=description,
                expected_count=template_item.expected_count,
                is_required=template_item.is_required,
                status=RequestItemStatus.PENDING,
            )
            self.db.add(request_item)
        
        self.db.commit()
        self.db.refresh(request_set)
        return request_set


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
        from app.models.documents import Document
        
        request_item = self.get(request_item_id)
        document = self.db.get(Document, document_id)
        
        if not request_item or not document:
            return False
        
        if document not in request_item.documents:
            request_item.documents.append(document)
            # Update status after linking
            self._update_item_status(request_item)
            self.db.commit()
        
        return True

    def unlink_document(self, request_item_id: int, document_id: int) -> bool:
        """Unlink a document from a request item."""
        from app.models.documents import Document
        
        request_item = self.get(request_item_id)
        document = self.db.get(Document, document_id)
        
        if not request_item or not document:
            return False
        
        if document in request_item.documents:
            request_item.documents.remove(document)
            # Update status after unlinking
            self._update_item_status(request_item)
            self.db.commit()
        
        return True

    def _update_item_status(self, request_item: RequestItem) -> None:
        """Update request item status based on document count."""
        doc_count = len(request_item.documents)
        # Normalize expected_count to avoid TypeError when it is None
        expected_count = (
            request_item.expected_count if request_item.expected_count is not None else 1
        )

        if doc_count == 0:
            request_item.status = RequestItemStatus.PENDING
        elif doc_count < expected_count:
            request_item.status = RequestItemStatus.PARTIAL
        else:
            request_item.status = RequestItemStatus.COMPLETE
