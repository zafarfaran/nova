"""AI tools/functions for the chat interface - using unified clients table."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.client import Client, EntityType
from app.models.documents import Document, DocumentStatus
from app.models.validation import ValidationResult, ValidationStatus
from app.schemas.email import EmailPurpose, EmailTone

# New schema models
from app.models.engagements import Engagement, EngagementType, EngagementStatus
from app.models.request_set import RequestSet, RequestSetStatus
from app.models.request_item import RequestItem, RequestItemStatus
from app.models.client_contact import ClientContact
from app.models.financial_account import FinancialAccount

logger = logging.getLogger(__name__)


# Tool definitions for function calling
TOOL_DEFINITIONS = [
    {
        "name": "list_clients",
        "description": "List all clients in the system",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_client_details",
        "description": "Get detailed information about a specific client including their VAT info, document checklist status, and bank connections",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "The ID of the client",
                },
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "search_clients",
        "description": "Search for clients by name or email",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to find clients by name or email",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_document_checklist",
        "description": "Get the document checklist status for a client, showing what documents are uploaded and what's missing",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "The ID of the client",
                },
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "get_clients_needing_attention",
        "description": "Get a list of clients who need attention due to missing documents, validation issues, or review stage",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "create_client",
        "description": "Create a new client in the system. Requires client name and email at minimum. Ask the user for VAT scheme and entity type if not provided.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {
                    "type": "string",
                    "description": "The name of the client/business (required)",
                },
                "email": {
                    "type": "string",
                    "description": "The client's email address (required)",
                },
                "entity_type": {
                    "type": "string",
                    "enum": ["sole_trader", "partnership", "llp", "limited_company", "plc", "charity", "other"],
                    "description": "The type of business entity",
                },
                "vat_scheme": {
                    "type": "string",
                    "enum": ["standard", "flat_rate", "cash_accounting", "annual_accounting"],
                    "description": "The VAT scheme the client uses",
                },
                "vat_number": {
                    "type": "string",
                    "description": "The client's VAT registration number",
                },
                "notes": {
                    "type": "string",
                    "description": "Any additional notes about the client",
                },
            },
            "required": ["client_name", "email"],
        },
    },
    {
        "name": "update_checklist_item",
        "description": "Update the status of a checklist item (e.g., mark as uploaded or missing)",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "integer",
                    "description": "The ID of the checklist item",
                },
                "status": {
                    "type": "string",
                    "enum": ["missing", "uploaded", "unknown"],
                    "description": "The new status for the item",
                },
            },
            "required": ["item_id", "status"],
        },
    },
    {
        "name": "send_email",
        "description": "Send an email to a client. The AI can generate professional email content based on the purpose and context. Use this to send reminders, request missing documents, notify about VAT returns, or send general communications.",
        "parameters": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "Recipient email address",
                },
                "to_name": {
                    "type": "string",
                    "description": "Recipient name (optional)",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject (optional - will be AI-generated if not provided)",
                },
                "body": {
                    "type": "string",
                    "description": "Email body (optional - will be AI-generated if not provided)",
                },
                "purpose": {
                    "type": "string",
                    "enum": ["reminder", "missing_documents", "vat_return_ready", "validation_issues", "invoice_request", "follow_up", "welcome", "general"],
                    "description": "The purpose of the email (used for AI generation if subject/body not provided)",
                },
                "tone": {
                    "type": "string",
                    "enum": ["formal", "professional", "friendly", "urgent"],
                    "description": "The tone of the email (default: professional)",
                },
                "client_id": {
                    "type": "integer",
                    "description": "Client ID for context (optional)",
                },
                "context_data": {
                    "type": "object",
                    "description": "Additional context for email generation (e.g., missing_items, due_date)",
                },
            },
            "required": ["to_email", "purpose"],
        },
    },
]


class ChatTools:
    """Executor for chat tools using unified clients table."""

    def __init__(self, db: Session):
        self.db = db

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return the result."""
        method = getattr(self, f"_tool_{tool_name}", None)
        if not method:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            logger.info(f"Executing tool {tool_name} with arguments: {arguments}")

            # Check if method is async
            import inspect
            if inspect.iscoroutinefunction(method):
                return await method(**arguments)
            else:
                return method(**arguments)
        except TypeError as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            logger.error(f"Arguments received: {arguments}")
            logger.error(f"Method signature: {inspect.signature(method)}")
            return {"error": f"Invalid arguments for {tool_name}: {str(e)}"}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

    def _tool_list_clients(self) -> dict[str, Any]:
        """List all clients."""
        clients = list(self.db.query(Client).order_by(Client.updated_at.desc()).all())
        return {
            "clients": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.contact_email,
                    "entity_type": c.entity_type.value if c.entity_type else None,
                    "vat_scheme": c.vat_scheme,
                    "vat_number": c.vat_number,
                }
                for c in clients
            ],
            "total": len(clients),
        }

    def _tool_get_client_details(self, client_id: int) -> dict[str, Any]:
        """Get detailed client information."""
        client = self.db.get(Client, client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        # Get latest Engagement
        latest_engagement = (
            self.db.query(Engagement)
            .filter(Engagement.client_id == client_id)
            .order_by(Engagement.period_end.desc())
            .first()
        )

        # Get RequestItems from engagement
        request_items_count = 0
        request_items_complete = 0
        if latest_engagement:
            request_sets = list(
                self.db.query(RequestSet)
                .filter(RequestSet.engagement_id == latest_engagement.id)
                .all()
            )
            for rs in request_sets:
                items = list(
                    self.db.query(RequestItem)
                    .filter(RequestItem.request_set_id == rs.id)
                    .all()
                )
                request_items_count += len(items)
                request_items_complete += len([i for i in items if i.status == RequestItemStatus.COMPLETE])

        # Get financial accounts
        financial_accounts = list(
            self.db.query(FinancialAccount)
            .filter(FinancialAccount.client_id == client_id, FinancialAccount.is_active == True)
            .all()
        )
        
        # Get client contacts
        contacts = list(
            self.db.query(ClientContact)
            .filter(ClientContact.client_id == client_id)
            .all()
        )

        # Build engagement info
        engagement_info = None
        if latest_engagement:
            quarter_num = (latest_engagement.period_start.month - 1) // 3 + 1
            engagement_info = {
                "id": latest_engagement.id,
                "type": latest_engagement.engagement_type.value if latest_engagement.engagement_type else None,
                "label": f"Q{quarter_num} {latest_engagement.period_start.year}",
                "start": latest_engagement.period_start.isoformat() if latest_engagement.period_start else None,
                "end": latest_engagement.period_end.isoformat() if latest_engagement.period_end else None,
                "due_date": latest_engagement.due_date.isoformat() if latest_engagement.due_date else None,
                "status": latest_engagement.status.value if latest_engagement.status else None,
            }
        
        # Calculate document stats
        documents_info = {
            "total_required": request_items_count,
            "uploaded": request_items_complete,
            "missing": request_items_count - request_items_complete,
            "completion_percentage": round(request_items_complete / request_items_count * 100) if request_items_count else 100,
        }

        return {
            "client": {
                "id": client.id,
                "name": client.name,
                "display_name": client.display_name,
                "email": client.contact_email,
                "contact_name": client.contact_name,
                "entity_type": client.entity_type.value if client.entity_type else None,
                "client_type": client.client_type,
                "vat_scheme": client.vat_scheme,
                "vat_number": client.vat_number,
                "vat_registered": client.vat_registered,
                "company_number": client.company_number,
                "utr": client.utr,
                "address": client.address,
                "notes": client.notes,
                "created_at": client.created_at.isoformat() if client.created_at else None,
            },
            "contacts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "role": c.role,
                    "is_primary": c.is_primary,
                }
                for c in contacts
            ],
            "vat_period": engagement_info,  # Use engagement as vat_period for backwards compat
            "engagement": engagement_info,
            "documents": documents_info,
            "financial_accounts": [
                {
                    "id": fa.id,
                    "provider": fa.provider,
                    "account_name": fa.account_name,
                    "account_type": fa.account_type.value if fa.account_type else None,
                    "currency": fa.currency_code,
                }
                for fa in financial_accounts
            ],
            "has_bank_connected": len(financial_accounts) > 0,
        }

    def _tool_search_clients(self, query: str) -> dict[str, Any]:
        """Search clients by name or email."""
        query_lower = query.lower()
        clients = list(
            self.db.query(Client)
            .filter(
                (Client.name.ilike(f"%{query_lower}%")) |
                (Client.contact_email.ilike(f"%{query_lower}%"))
            )
            .limit(10)
            .all()
        )

        if not clients:
            return {"message": f"No clients found matching '{query}'", "clients": [], "total": 0}

        return {
            "clients": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.contact_email,
                    "entity_type": c.entity_type.value if c.entity_type else None,
                    "vat_scheme": c.vat_scheme,
                }
                for c in clients
            ],
            "total": len(clients),
        }

    def _tool_get_document_checklist(self, client_id: int) -> dict[str, Any]:
        """Get document checklist for a client using RequestItems from engagements."""
        client = self.db.get(Client, client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        # Get latest Engagement
        latest_engagement = (
            self.db.query(Engagement)
            .filter(Engagement.client_id == client_id)
            .order_by(Engagement.period_end.desc())
            .first()
        )
        
        request_items_list = []
        if latest_engagement:
            request_sets = list(
                self.db.query(RequestSet)
                .filter(RequestSet.engagement_id == latest_engagement.id)
                .all()
            )
            for rs in request_sets:
                items = list(
                    self.db.query(RequestItem)
                    .filter(RequestItem.request_set_id == rs.id)
                    .all()
                )
                for item in items:
                    status_icon = "✅" if item.status == RequestItemStatus.COMPLETE else (
                        "⏳" if item.status == RequestItemStatus.PARTIAL else "❌"
                    )
                    request_items_list.append({
                        "id": item.id,
                        "title": item.document_type.name if item.document_type else item.description,
                        "description": item.description,
                        "status": item.status.value if item.status else "pending",
                        "status_icon": status_icon,
                        "required": item.is_required,
                        "expected_count": item.expected_count,
                        "documents_count": len(item.documents) if item.documents else 0,
                        "request_set": rs.name,
                    })
        
        financial_accounts = list(
            self.db.query(FinancialAccount)
            .filter(FinancialAccount.client_id == client_id, FinancialAccount.is_active == True)
            .all()
        )

        required = [i for i in request_items_list if i.get("required", True)]
        uploaded = [i for i in required if i["status"] in ("uploaded", "complete")]

        return {
            "client_name": client.name,
            "checklist": request_items_list,
            "summary": {
                "total_items": len(request_items_list),
                "required_items": len(required),
                "uploaded": len(uploaded),
                "missing": len(required) - len(uploaded),
                "completion_percentage": round(len(uploaded) / len(required) * 100) if required else 100,
            },
            "has_bank_connected": len(financial_accounts) > 0,
            "engagement": {
                "id": latest_engagement.id,
                "type": latest_engagement.engagement_type.value,
                "status": latest_engagement.status.value,
            } if latest_engagement else None,
        }

    def _tool_get_clients_needing_attention(self) -> dict[str, Any]:
        """Get clients with missing documents, validation issues, or in review."""
        clients = list(self.db.query(Client).all())

        needs_attention = []
        for client in clients:
            # Get latest engagement
            latest_engagement = (
                self.db.query(Engagement)
                .filter(Engagement.client_id == client.id)
                .order_by(Engagement.period_end.desc())
                .first()
            )

            # Get request items from engagement
            documents_required = 0
            documents_uploaded = 0
            missing_items = []
            
            if latest_engagement:
                request_sets = list(
                    self.db.query(RequestSet)
                    .filter(RequestSet.engagement_id == latest_engagement.id)
                    .all()
                )
                for rs in request_sets:
                    items = list(
                        self.db.query(RequestItem)
                        .filter(RequestItem.request_set_id == rs.id, RequestItem.is_required == True)
                        .all()
                    )
                    documents_required += len(items)
                    for item in items:
                        if item.status == RequestItemStatus.COMPLETE:
                            documents_uploaded += 1
                        else:
                            missing_items.append(item.description or (item.document_type.name if item.document_type else "Unknown"))

            validation_issue_count = 0
            pending_review_count = 0
            has_failed_validations = False
            has_pending_reviews = False

            if latest_engagement:
                # Get validation issues for documents in this engagement
                validation_rows = list(
                    self.db.query(
                        Document.id,
                        ValidationResult.status,
                        ValidationResult.review_action,
                    )
                    .join(ValidationResult, ValidationResult.document_id == Document.id)
                    .filter(
                        Document.engagement_id == latest_engagement.id,
                        ValidationResult.status.in_([
                            ValidationStatus.FAILED,
                            ValidationStatus.WARNING,
                        ]),
                    )
                    .all()
                )

                validation_doc_ids: set[int] = set()
                pending_review_doc_ids: set[int] = set()
                for doc_id, status, review_action in validation_rows:
                    validation_doc_ids.add(doc_id)
                    if review_action is None:
                        pending_review_doc_ids.add(doc_id)
                    if status == ValidationStatus.FAILED:
                        has_failed_validations = True

                failed_doc_ids = {
                    doc_id
                    for (doc_id,) in (
                        self.db.query(Document.id)
                        .filter(
                            Document.engagement_id == latest_engagement.id,
                            Document.status == DocumentStatus.FAILED,
                        )
                        .all()
                    )
                }

                validation_issue_count = len(validation_doc_ids | failed_doc_ids)
                pending_review_count = len(pending_review_doc_ids)

                if failed_doc_ids:
                    has_failed_validations = True

            has_pending_reviews = pending_review_count > 0

            # Check for financial accounts
            bank_connected = (
                self.db.query(FinancialAccount)
                .filter(FinancialAccount.client_id == client.id, FinancialAccount.is_active == True)
                .count()
                > 0
            )

            attention_reasons = []
            if missing_items:
                attention_reasons.append("missing_documents")
            if validation_issue_count > 0:
                attention_reasons.append("validation_issues")
            if has_pending_reviews:
                attention_reasons.append("pending_review")
            if latest_engagement and latest_engagement.status == EngagementStatus.UNDER_REVIEW:
                attention_reasons.append("under_review")

            if attention_reasons:
                needs_attention.append({
                    "id": client.id,
                    "name": client.name,
                    "email": client.contact_email,
                    "missing_documents": len(missing_items),
                    "missing_items": missing_items[:3],
                    "documents_required": documents_required,
                    "documents_uploaded": documents_uploaded,
                    "has_bank_connection": bank_connected,
                    "engagement_status": latest_engagement.status.value if latest_engagement else None,
                    "validation_issue_count": validation_issue_count,
                    "pending_review_count": pending_review_count,
                    "has_failed_validations": has_failed_validations,
                    "has_pending_reviews": has_pending_reviews,
                    "attention_reasons": attention_reasons,
                })

        return {
            "clients_needing_attention": needs_attention,
            "total": len(needs_attention),
            "message": (
                f"{len(needs_attention)} client(s) need attention"
                if needs_attention
                else "All clients are up to date!"
            ),
        }

    async def _tool_create_client(
        self,
        client_name: str | None = None,
        email: str | None = None,
        name: str | None = None,  # Alternative parameter name
        entity_type: str = "limited_company",
        vat_scheme: str = "standard",
        vat_number: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a new client."""
        # Handle both 'client_name' and 'name' parameter names
        if not client_name and name:
            client_name = name

        if not client_name or not email:
            logger.warning(f"create_client called without required params: client_name={client_name}, email={email}")
            return {"error": "Both client_name (business name) and email are required to create a client. Please ask the user for these details."}

        logger.info(f"Creating client: {client_name}, email: {email}")
        # Check if client with same email already exists
        existing = self.db.query(Client).filter(Client.contact_email == email).first()
        if existing:
            return {
                "error": f"A client with email '{email}' already exists",
                "existing_client": {
                    "id": existing.id,
                    "name": existing.name,
                    "email": existing.contact_email,
                },
            }

        # Check if VAT number already exists
        if vat_number:
            existing_vat = self.db.query(Client).filter(Client.vat_number == vat_number).first()
            if existing_vat:
                return {
                    "error": f"A client with VAT number '{vat_number}' already exists",
                    "existing_client": {
                        "id": existing_vat.id,
                        "name": existing_vat.name,
                    },
                }

        # Map entity type string to enum
        try:
            entity_type_enum = EntityType(entity_type)
        except ValueError:
            entity_type_enum = EntityType.LIMITED_COMPANY

        # Create the client
        client = Client(
            name=client_name,
            contact_email=email,
            entity_type=entity_type_enum,
            vat_scheme=vat_scheme,
            vat_number=vat_number,
            notes=notes,
            sales_channels=[],
        )
        self.db.add(client)
        self.db.flush()  # Get the client ID

        # Create default engagement (current quarter)
        now = datetime.now()
        quarter_month = ((now.month - 1) // 3) * 3 + 1
        period_start = datetime(now.year, quarter_month, 1)

        quarter_end_month = ((now.month - 1) // 3) * 3 + 3
        if quarter_end_month == 3:
            period_end = datetime(now.year, 3, 31)
        elif quarter_end_month == 6:
            period_end = datetime(now.year, 6, 30)
        elif quarter_end_month == 9:
            period_end = datetime(now.year, 9, 30)
        else:
            period_end = datetime(now.year, 12, 31)

        engagement = Engagement(
            client_id=client.id,
            engagement_type=EngagementType.VAT_RETURN,
            period_start=period_start.date(),
            period_end=period_end.date(),
            status=EngagementStatus.DRAFT,
        )
        self.db.add(engagement)
        self.db.flush()

        # Create default request set with items
        request_set = RequestSet(
            engagement_id=engagement.id,
            name="Document Collection",
            status=RequestSetStatus.OPEN,
        )
        self.db.add(request_set)
        self.db.flush()

        # Create default request items
        default_items = [
            {"description": "Bank Statements", "required": True},
            {"description": "Sales Invoices", "required": True},
            {"description": "Purchase Invoices", "required": True},
            {"description": "Expense Receipts", "required": True},
            {"description": "Payroll Records", "required": False},
        ]

        for item in default_items:
            request_item = RequestItem(
                request_set_id=request_set.id,
                description=item["description"],
                is_required=item["required"],
                expected_count=1,
                status=RequestItemStatus.PENDING,
            )
            self.db.add(request_item)

        self.db.commit()
        self.db.refresh(client)

        quarter_num = (period_start.month - 1) // 3 + 1
        engagement_label = f"Q{quarter_num} {period_start.year}"

        onboarding_link = f"/onboard/{client.id}"

        # Send welcome email asynchronously
        try:
            from app.services.email import EmailNotificationService
            email_notif_service = EmailNotificationService(db=self.db)
            await email_notif_service.send_welcome_email(
                client_id=client.id,
                onboarding_link=onboarding_link
            )
            logger.info(f"Welcome email sent to new client {client.name}")
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}", exc_info=True)
            # Don't fail client creation if email fails

        return {
            "success": True,
            "message": f"Client '{client_name}' created successfully. Welcome email sent to {email}.",
            "client": {
                "id": client.id,
                "name": client.name,
                "email": client.contact_email,
                "entity_type": client.entity_type.value,
                "vat_scheme": client.vat_scheme,
                "engagement": engagement_label,
            },
            "onboarding_link": onboarding_link,
        }

    def _tool_update_checklist_item(self, item_id: int, status: str) -> dict[str, Any]:
        """Update a request item status."""
        request_item = self.db.get(RequestItem, item_id)
        if request_item:
            # Map status strings to RequestItemStatus enum
            status_mapping = {
                "missing": RequestItemStatus.PENDING,
                "uploaded": RequestItemStatus.COMPLETE,
                "unknown": RequestItemStatus.PENDING,
                "pending": RequestItemStatus.PENDING,
                "partial": RequestItemStatus.PARTIAL,
                "complete": RequestItemStatus.COMPLETE,
                "waived": RequestItemStatus.WAIVED,
            }
            
            new_status = status_mapping.get(status.lower())
            if not new_status:
                valid_statuses = list(status_mapping.keys())
                return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"}
            
            request_item.status = new_status
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Request item updated to '{new_status.value}'",
                "item": {
                    "id": request_item.id,
                    "description": request_item.description,
                    "status": request_item.status.value,
                },
            }
        
        return {"error": f"Request item {item_id} not found"}

    async def _tool_send_email(
        self,
        to_email: str,
        purpose: str,
        to_name: str | None = None,
        subject: str | None = None,
        body: str | None = None,
        tone: str = "professional",
        client_id: int | None = None,
        context_data: dict | None = None,
    ) -> dict[str, Any]:
        """Send an email to a client."""
        from app.ai import get_ai_provider
        from app.schemas.email import EmailRequest
        from app.services.email import EmailService

        logger.info(f"Tool send_email called: to={to_email}, purpose={purpose}, tone={tone}")

        # Convert string enums to proper enum types
        try:
            email_purpose = EmailPurpose(purpose)
            email_tone = EmailTone(tone)
        except ValueError as e:
            logger.error(f"Invalid purpose or tone: {e}")
            return {"error": f"Invalid purpose or tone: {str(e)}"}

        # Create email request
        email_request = EmailRequest(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body=body,
            purpose=email_purpose,
            tone=email_tone,
            client_id=client_id,
            context_data=context_data,
        )

        # Send email using email service
        try:
            ai_provider = get_ai_provider()
            email_service = EmailService(db=self.db, ai_provider=ai_provider)

            logger.info("Calling email service to send email...")
            response = await email_service.send_email(email_request)
            logger.info(f"Email service response: success={response.success}")

            if response.success:
                return {
                    "success": True,
                    "message": f"Email sent successfully to {to_email}",
                    "subject": response.generated_subject or subject,
                    "sent_at": response.sent_at.isoformat() if response.sent_at else None,
                }
            else:
                return {
                    "success": False,
                    "error": response.message,
                }
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}",
            }
