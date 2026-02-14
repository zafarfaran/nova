"""Service layer for Chaser operations."""

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.models.chaser import ChaserRequest, ChaserResponse, ChaserStatus
from app.models.request_set import RequestSet, RequestSetStatus
from app.models.request_item import RequestItem, RequestItemStatus
from app.schemas.email import EmailPurpose, EmailRequest, EmailTone
from app.services.email import EmailService


class ChaserService:
    """Service for managing chaser requests."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        engagement_id: int,
        recipient_email: str,
        recipient_name: str | None = None,
        requested_items: list[str] | None = None,
        due_date: date | None = None,
    ) -> ChaserRequest:
        """Create a new chaser request."""
        if due_date is None:
            due_date = date.today() + timedelta(days=14)  # Default 2 weeks

        chaser = ChaserRequest(
            engagement_id=engagement_id,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            requested_items=requested_items or [],
            due_date=due_date,
        )
        self.db.add(chaser)
        self.db.commit()
        self.db.refresh(chaser)
        return chaser

    def get(self, chaser_id: int) -> ChaserRequest | None:
        """Get a chaser request by ID."""
        return self.db.get(ChaserRequest, chaser_id)

    def get_by_token(self, upload_token: str) -> ChaserRequest | None:
        """Get a chaser request by upload token."""
        stmt = select(ChaserRequest).where(ChaserRequest.upload_token == upload_token)
        return self.db.scalars(stmt).first()

    def list_by_engagement(
        self, engagement_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[ChaserRequest], int]:
        """List all chaser requests for an engagement."""
        stmt = (
            select(ChaserRequest)
            .where(ChaserRequest.engagement_id == engagement_id)
            .offset(skip)
            .limit(limit)
        )
        chasers = list(self.db.scalars(stmt).all())
        total = (
            self.db.query(func.count(ChaserRequest.id))
            .filter(ChaserRequest.engagement_id == engagement_id)
            .scalar()
        )
        return chasers, total or 0

    async def generate_message(self, chaser_id: int) -> ChaserRequest | None:
        """Generate AI message for a chaser request."""
        chaser = self.get(chaser_id)
        if not chaser:
            return None

        ai_provider = get_ai_provider()
        message = await ai_provider.generate_chaser_message(
            missing_items=chaser.requested_items,
            recipient_name=chaser.recipient_name or "Client",
            due_date=str(chaser.due_date) if chaser.due_date else "as soon as possible",
        )

        chaser.message_body = message
        chaser.subject = f"Document Request - {len(chaser.requested_items)} items needed"

        self.db.commit()
        self.db.refresh(chaser)
        return chaser

    async def send_chaser_email(self, chaser_id: int) -> ChaserRequest | None:
        """Generate message (if needed) and send the chaser email."""
        chaser = self.get(chaser_id)
        if not chaser:
            return None

        # Generate message if not already generated
        if not chaser.message_body or not chaser.subject:
            chaser = await self.generate_message(chaser_id)
            if not chaser:
                return None

        # Send the email
        ai_provider = get_ai_provider()
        email_service = EmailService(db=self.db, ai_provider=ai_provider)

        email_request = EmailRequest(
            to_email=chaser.recipient_email,
            to_name=chaser.recipient_name,
            subject=chaser.subject,
            body=chaser.message_body,
            purpose=EmailPurpose.MISSING_DOCUMENTS,
            tone=EmailTone.PROFESSIONAL,
        )

        response = await email_service.send_email(email_request)

        if response.success:
            # Mark as sent
            chaser.status = ChaserStatus.SENT
            chaser.sent_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(chaser)

        return chaser

    def mark_sent(self, chaser_id: int) -> ChaserRequest | None:
        """Mark a chaser request as sent (without actually sending email)."""
        chaser = self.get(chaser_id)
        if not chaser:
            return None

        chaser.status = ChaserStatus.SENT
        chaser.sent_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(chaser)
        return chaser

    def mark_reminded(self, chaser_id: int) -> ChaserRequest | None:
        """Mark a chaser request as reminded."""
        chaser = self.get(chaser_id)
        if not chaser:
            return None

        chaser.status = ChaserStatus.REMINDED
        chaser.last_reminded_at = datetime.utcnow()
        chaser.reminder_count += 1

        self.db.commit()
        self.db.refresh(chaser)
        return chaser

    def auto_chase(self, engagement_id: int, recipient_email: str) -> ChaserRequest | None:
        """Automatically create a chaser for all pending request items in an engagement."""
        # Find pending request items
        stmt = (
            select(RequestItem)
            .join(RequestSet)
            .where(
                RequestSet.engagement_id == engagement_id,
                RequestItem.status == RequestItemStatus.PENDING,
            )
        )
        pending_items = list(self.db.scalars(stmt).all())

        if not pending_items:
            return None

        requested_items = [
            f"{item.description or 'Document'}: {item.expected_count} item(s) needed"
            for item in pending_items
        ]

        chaser = self.create(
            engagement_id=engagement_id,
            recipient_email=recipient_email,
            requested_items=requested_items,
        )

        return chaser

    def record_response(
        self,
        chaser_id: int,
        documents_uploaded: int,
        responder_email: str | None = None,
        responder_name: str | None = None,
        notes: str | None = None,
    ) -> ChaserResponse:
        """Record a response to a chaser request."""
        response = ChaserResponse(
            chaser_request_id=chaser_id,
            responder_email=responder_email,
            responder_name=responder_name,
            documents_uploaded=documents_uploaded,
            notes=notes,
        )
        self.db.add(response)

        # Update chaser status
        chaser = self.get(chaser_id)
        if chaser:
            if documents_uploaded >= len(chaser.requested_items):
                chaser.status = ChaserStatus.COMPLETE
            else:
                chaser.status = ChaserStatus.PARTIALLY_RECEIVED

        self.db.commit()
        self.db.refresh(response)
        return response
