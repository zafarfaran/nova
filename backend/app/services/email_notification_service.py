"""Email notification service for automated emails throughout the application."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.config import get_settings
from app.models.client import Client
from app.models.document import Document
from app.models.validation import ValidationResult, ValidationStatus
from app.schemas.email import EmailPurpose, EmailRequest, EmailTone
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending automated email notifications."""

    def __init__(self, db: Session):
        self.db = db
        self.ai_provider = get_ai_provider()
        self.email_service = EmailService(db=db, ai_provider=self.ai_provider)

    async def send_welcome_email(self, client_id: int, onboarding_link: str | None = None) -> bool:
        """Send welcome email to a newly created client.

        Args:
            client_id: ID of the client
            onboarding_link: Optional onboarding link to include

        Returns:
            True if email sent successfully
        """
        client = self.db.get(Client, client_id)
        if not client or not client.contact_email:
            logger.warning(f"Cannot send welcome email: client {client_id} not found or no email")
            return False

        logger.info(f"Sending welcome email to client {client.name} ({client.contact_email})")

        # Get app URL from settings
        settings = get_settings()
        base_url = settings.app_url.rstrip('/')

        # Build full URL
        if onboarding_link:
            # If it's a relative path, make it absolute
            if onboarding_link.startswith('/'):
                full_url = f"{base_url}{onboarding_link}"
            else:
                full_url = onboarding_link
        else:
            # Default to client dashboard
            full_url = f"{base_url}/client/{client_id}/dashboard"

        # Build comprehensive context for AI
        context_data: dict[str, Any] = {
            "company_name": client.name,
            "contact_name": client.contact_name or "there",
            "vat_scheme": client.vat_scheme or "standard",
            "entity_type": client.entity_type.value if client.entity_type else "limited company",
            "onboarding_url": full_url,
            "steps": [
                "1. Click the link below to access your personalized dashboard",
                "2. Review your VAT period and document checklist",
                "3. Upload required documents (bank statements, invoices, receipts, etc.)",
                "4. Our AI will automatically validate your documents",
                "5. Review validation results and make any necessary corrections",
                "6. Submit for final review when all documents are ready"
            ],
            "required_documents": [
                "Bank statements for the VAT period",
                "Sales invoices and credit notes",
                "Purchase invoices and receipts",
                "Payroll records (if applicable)",
                "Any other relevant VAT documentation"
            ],
            "benefits": [
                "Automated document validation using AI",
                "Real-time compliance checking",
                "Instant feedback on any issues",
                "Streamlined VAT return preparation",
                "Secure document storage"
            ],
            "support_info": "If you have any questions, simply reply to this email or contact our support team.",
        }

        email_request = EmailRequest(
            to_email=client.contact_email,
            to_name=client.contact_name or client.name,
            purpose=EmailPurpose.WELCOME,
            tone=EmailTone.FRIENDLY,
            client_id=client_id,
            context_data=context_data,
        )

        try:
            response = await self.email_service.send_email(email_request)
            if response.success:
                logger.info(f"Welcome email sent successfully to {client.contact_email}")
                return True
            else:
                logger.error(f"Failed to send welcome email: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}", exc_info=True)
            return False

    async def send_validation_failure_email(
        self, document_id: int, validation_results: list[ValidationResult]
    ) -> bool:
        """Send email when document validation fails.

        Args:
            document_id: ID of the document
            validation_results: List of validation results

        Returns:
            True if email sent successfully
        """
        document = self.db.get(Document, document_id)
        if not document or not document.evidence_item:
            logger.warning(f"Cannot send validation email: document {document_id} not found")
            return False

        # Get client through evidence item -> vat period -> client
        evidence_item = document.evidence_item
        if not evidence_item or not evidence_item.vat_period:
            logger.warning(f"Cannot send validation email: missing evidence/period for doc {document_id}")
            return False

        vat_period = evidence_item.vat_period
        client = vat_period.client
        if not client or not client.contact_email:
            logger.warning(f"Cannot send validation email: client not found or no email")
            return False

        # Collect validation issues
        failed_validations = [r for r in validation_results if r.status == ValidationStatus.FAILED]
        warning_validations = [r for r in validation_results if r.status == ValidationStatus.WARNING]

        if not failed_validations and not warning_validations:
            logger.info(f"No validation issues for document {document_id}, skipping email")
            return False

        logger.info(f"Sending validation failure email to {client.contact_email} for document {document.filename}")

        issues = []
        for result in failed_validations:
            issues.append(f"❌ {result.message or result.rule_type.value}")

        for result in warning_validations:
            issues.append(f"⚠️ {result.message or result.rule_type.value}")

        context_data = {
            "document_name": document.filename,
            "document_type": document.document_type.value if document.document_type else "document",
            "issues": issues,
            "issue_count": len(issues),
            "vat_period": f"Q{((vat_period.period_start.month - 1) // 3) + 1} {vat_period.period_start.year}" if vat_period.period_start else "current period",
            "call_to_action": "Please review and re-upload the corrected document.",
        }

        email_request = EmailRequest(
            to_email=client.contact_email,
            to_name=client.contact_name or client.name,
            purpose=EmailPurpose.VALIDATION_ISSUES,
            tone=EmailTone.PROFESSIONAL,
            client_id=client.id,
            context_data=context_data,
        )

        try:
            response = await self.email_service.send_email(email_request)
            if response.success:
                logger.info(f"Validation failure email sent successfully to {client.contact_email}")
                return True
            else:
                logger.error(f"Failed to send validation failure email: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Error sending validation failure email: {e}", exc_info=True)
            return False

    async def send_document_rejection_email(
        self,
        document_id: int,
        rejected_by: str,
        rejection_reason: str,
    ) -> bool:
        """Send email when accountant rejects a document.

        Args:
            document_id: ID of the rejected document
            rejected_by: Name of person who rejected it
            rejection_reason: Reason for rejection

        Returns:
            True if email sent successfully
        """
        document = self.db.get(Document, document_id)
        if not document or not document.evidence_item:
            logger.warning(f"Cannot send rejection email: document {document_id} not found")
            return False

        evidence_item = document.evidence_item
        if not evidence_item or not evidence_item.vat_period:
            logger.warning(f"Cannot send rejection email: missing evidence/period for doc {document_id}")
            return False

        vat_period = evidence_item.vat_period
        client = vat_period.client
        if not client or not client.contact_email:
            logger.warning(f"Cannot send rejection email: client not found or no email")
            return False

        logger.info(f"Sending rejection email to {client.contact_email} for document {document.filename}")

        context_data = {
            "document_name": document.filename,
            "document_type": document.document_type.value if document.document_type else "document",
            "rejected_by": rejected_by,
            "rejection_reason": rejection_reason,
            "vat_period": f"Q{((vat_period.period_start.month - 1) // 3) + 1} {vat_period.period_start.year}" if vat_period.period_start else "current period",
            "call_to_action": "Please upload a corrected version of this document.",
        }

        email_request = EmailRequest(
            to_email=client.contact_email,
            to_name=client.contact_name or client.name,
            subject=f"Document Rejected: {document.filename}",
            purpose=EmailPurpose.VALIDATION_ISSUES,
            tone=EmailTone.PROFESSIONAL,
            client_id=client.id,
            context_data=context_data,
        )

        try:
            response = await self.email_service.send_email(email_request)
            if response.success:
                logger.info(f"Rejection email sent successfully to {client.contact_email}")
                return True
            else:
                logger.error(f"Failed to send rejection email: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Error sending rejection email: {e}", exc_info=True)
            return False

    async def send_missing_documents_email(
        self,
        client_id: int,
        missing_items: list[str],
        due_date: str | None = None,
    ) -> bool:
        """Send email about missing documents.

        Args:
            client_id: ID of the client
            missing_items: List of missing document types
            due_date: Optional due date

        Returns:
            True if email sent successfully
        """
        client = self.db.get(Client, client_id)
        if not client or not client.contact_email:
            logger.warning(f"Cannot send missing documents email: client {client_id} not found or no email")
            return False

        logger.info(f"Sending missing documents email to {client.contact_email}")

        context_data = {
            "missing_items": missing_items,
            "missing_count": len(missing_items),
            "due_date": due_date or "as soon as possible",
            "call_to_action": "Please upload the missing documents to complete your VAT return.",
        }

        email_request = EmailRequest(
            to_email=client.contact_email,
            to_name=client.contact_name or client.name,
            purpose=EmailPurpose.MISSING_DOCUMENTS,
            tone=EmailTone.PROFESSIONAL,
            client_id=client_id,
            context_data=context_data,
        )

        try:
            response = await self.email_service.send_email(email_request)
            if response.success:
                logger.info(f"Missing documents email sent successfully to {client.contact_email}")
                return True
            else:
                logger.error(f"Failed to send missing documents email: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Error sending missing documents email: {e}", exc_info=True)
            return False

    async def send_vat_return_ready_email(self, client_id: int, period_id: int) -> bool:
        """Send email when VAT return is ready for review.

        Args:
            client_id: ID of the client
            period_id: ID of the VAT period

        Returns:
            True if email sent successfully
        """
        from app.models.vat_period import VATPeriod

        client = self.db.get(Client, client_id)
        period = self.db.get(VATPeriod, period_id)

        if not client or not client.contact_email:
            logger.warning(f"Cannot send VAT ready email: client {client_id} not found or no email")
            return False

        if not period:
            logger.warning(f"Cannot send VAT ready email: period {period_id} not found")
            return False

        logger.info(f"Sending VAT return ready email to {client.contact_email}")

        context_data = {
            "vat_period": f"Q{((period.period_start.month - 1) // 3) + 1} {period.period_start.year}" if period.period_start else "current period",
            "period_start": period.period_start.isoformat() if period.period_start else None,
            "period_end": period.period_end.isoformat() if period.period_end else None,
            "due_date": period.due_date.isoformat() if period.due_date else None,
            "call_to_action": "Please review and approve your VAT return in the portal.",
        }

        email_request = EmailRequest(
            to_email=client.contact_email,
            to_name=client.contact_name or client.name,
            purpose=EmailPurpose.VAT_RETURN_READY,
            tone=EmailTone.PROFESSIONAL,
            client_id=client_id,
            context_data=context_data,
        )

        try:
            response = await self.email_service.send_email(email_request)
            if response.success:
                logger.info(f"VAT return ready email sent successfully to {client.contact_email}")
                return True
            else:
                logger.error(f"Failed to send VAT return ready email: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Error sending VAT return ready email: {e}", exc_info=True)
            return False
