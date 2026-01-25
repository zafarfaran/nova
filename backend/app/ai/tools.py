"""AI tools/functions for the chat interface - using unified clients table."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.client import Client, EntityType
from app.models.vat_period import VATPeriod, PeriodStatus
from app.models.bank_connection import BankConnection
from app.models.checklist_item import ChecklistItem
from app.models.document import Document, DocumentStatus
from app.models.evidence import EvidenceItem
from app.models.validation import ValidationResult, ValidationStatus
from app.schemas.email import EmailPurpose, EmailTone

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

        # Get latest VAT period
        latest_period = (
            self.db.query(VATPeriod)
            .filter(VATPeriod.client_id == client_id)
            .order_by(VATPeriod.period_end.desc())
            .first()
        )

        # Get checklist summary
        checklist_items = list(
            self.db.query(ChecklistItem)
            .filter(ChecklistItem.client_id == client_id)
            .all()
        )
        required_items = [i for i in checklist_items if i.required]
        uploaded_items = [i for i in required_items if i.status == "uploaded"]

        # Get bank connections
        bank_connections = list(
            self.db.query(BankConnection)
            .filter(BankConnection.client_id == client_id, BankConnection.is_active == True)
            .all()
        )

        vat_period_info = None
        if latest_period:
            quarter_num = (latest_period.period_start.month - 1) // 3 + 1
            vat_period_info = {
                "label": f"Q{quarter_num} {latest_period.period_start.year}",
                "start": latest_period.period_start.isoformat() if latest_period.period_start else None,
                "end": latest_period.period_end.isoformat() if latest_period.period_end else None,
                "due_date": latest_period.due_date.isoformat() if latest_period.due_date else None,
                "status": latest_period.status.value if latest_period.status else None,
            }

        return {
            "client": {
                "id": client.id,
                "name": client.name,
                "email": client.contact_email,
                "contact_name": client.contact_name,
                "entity_type": client.entity_type.value if client.entity_type else None,
                "vat_scheme": client.vat_scheme,
                "vat_number": client.vat_number,
                "address": client.address,
                "notes": client.notes,
                "created_at": client.created_at.isoformat() if client.created_at else None,
            },
            "vat_period": vat_period_info,
            "documents": {
                "total_required": len(required_items),
                "uploaded": len(uploaded_items),
                "missing": len(required_items) - len(uploaded_items),
                "completion_percentage": round(len(uploaded_items) / len(required_items) * 100) if required_items else 100,
            },
            "bank_connections": [
                {
                    "institution": bc.institution_name,
                    "account_name": bc.account_name,
                    "account_type": bc.account_type,
                }
                for bc in bank_connections
            ],
            "has_bank_connected": len(bank_connections) > 0,
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
        """Get document checklist for a client."""
        client = self.db.get(Client, client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        checklist_items = list(
            self.db.query(ChecklistItem)
            .filter(ChecklistItem.client_id == client_id)
            .all()
        )

        bank_connections = list(
            self.db.query(BankConnection)
            .filter(BankConnection.client_id == client_id, BankConnection.is_active == True)
            .all()
        )

        items = []
        for item in checklist_items:
            status_icon = "✅" if item.status == "uploaded" else ("⏳" if item.status == "unknown" else "❌")
            items.append({
                "id": item.id,
                "title": item.title,
                "status": item.status,
                "status_icon": status_icon,
                "required": item.required,
                "has_file": item.uploaded_file_url is not None,
            })

        required = [i for i in items if i["required"]]
        uploaded = [i for i in required if i["status"] == "uploaded"]

        return {
            "client_name": client.name,
            "checklist": items,
            "summary": {
                "total_items": len(items),
                "required_items": len(required),
                "uploaded": len(uploaded),
                "missing": len(required) - len(uploaded),
                "completion_percentage": round(len(uploaded) / len(required) * 100) if required else 100,
            },
            "has_bank_connected": len(bank_connections) > 0,
        }

    def _tool_get_clients_needing_attention(self) -> dict[str, Any]:
        """Get clients with missing documents, validation issues, or in review."""
        clients = list(self.db.query(Client).all())

        needs_attention = []
        for client in clients:
            checklist_items = list(
                self.db.query(ChecklistItem)
                .filter(
                    ChecklistItem.client_id == client.id,
                    ChecklistItem.required == True,
                    ChecklistItem.status != "uploaded"
                )
                .all()
            )

            required_items = list(
                self.db.query(ChecklistItem)
                .filter(
                    ChecklistItem.client_id == client.id,
                    ChecklistItem.required == True,
                )
                .all()
            )
            uploaded_items = [i for i in required_items if i.status == "uploaded"]

            latest_period = (
                self.db.query(VATPeriod)
                .filter(VATPeriod.client_id == client.id)
                .order_by(VATPeriod.period_end.desc())
                .first()
            )

            documents_required = len(required_items)
            documents_uploaded = len(uploaded_items)
            if documents_required == 0 and latest_period:
                evidence_items = list(
                    self.db.query(EvidenceItem)
                    .filter(EvidenceItem.vat_period_id == latest_period.id)
                    .all()
                )
                documents_required = sum(item.expected_count for item in evidence_items)
                documents_uploaded = sum(item.received_count for item in evidence_items)

            validation_issue_count = 0
            pending_review_count = 0
            failed_document_count = 0
            has_failed_validations = False
            has_pending_reviews = False

            if latest_period:
                validation_rows = list(
                    self.db.query(
                        Document.id,
                        ValidationResult.status,
                        ValidationResult.review_action,
                    )
                    .join(ValidationResult, ValidationResult.document_id == Document.id)
                    .join(EvidenceItem, Document.evidence_item_id == EvidenceItem.id)
                    .filter(
                        EvidenceItem.vat_period_id == latest_period.id,
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
                        .join(EvidenceItem, Document.evidence_item_id == EvidenceItem.id)
                        .filter(
                            EvidenceItem.vat_period_id == latest_period.id,
                            Document.status == DocumentStatus.FAILED,
                        )
                        .all()
                    )
                }

                failed_document_count = len(failed_doc_ids)
                validation_issue_count = len(validation_doc_ids | failed_doc_ids)
                pending_review_count = len(pending_review_doc_ids)

                if failed_doc_ids:
                    has_failed_validations = True

            has_pending_reviews = pending_review_count > 0

            bank_connected = (
                self.db.query(BankConnection)
                .filter(BankConnection.client_id == client.id, BankConnection.is_active == True)
                .count()
                > 0
            )

            attention_reasons = []
            if checklist_items:
                attention_reasons.append("missing_documents")
            if validation_issue_count > 0:
                attention_reasons.append("validation_issues")
            if has_pending_reviews:
                attention_reasons.append("pending_review")
            if latest_period and latest_period.status == PeriodStatus.UNDER_REVIEW:
                attention_reasons.append("under_review")

            if attention_reasons:
                needs_attention.append({
                    "id": client.id,
                    "name": client.name,
                    "email": client.contact_email,
                    "missing_documents": len(checklist_items),
                    "missing_items": [item.title for item in checklist_items[:3]],
                    "documents_required": documents_required,
                    "documents_uploaded": documents_uploaded,
                    "has_bank_connection": bank_connected,
                    "vat_period_status": latest_period.status.value if latest_period else None,
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

        # Create default VAT period (current quarter)
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

        vat_period = VATPeriod(
            client_id=client.id,
            period_start=period_start.date(),
            period_end=period_end.date(),
            status=PeriodStatus.DRAFT,
            is_locked=False,
        )
        self.db.add(vat_period)

        # Create default checklist items
        default_checklist = [
            {"item_id": "bank_statements", "title": "Bank Statements", "required": True},
            {"item_id": "sales_invoices", "title": "Sales Invoices", "required": True},
            {"item_id": "purchase_invoices", "title": "Purchase Invoices", "required": True},
            {"item_id": "expense_receipts", "title": "Expense Receipts", "required": True},
            {"item_id": "payroll_records", "title": "Payroll Records", "required": False},
        ]

        for item in default_checklist:
            checklist_item = ChecklistItem(
                client_id=client.id,
                item_id=item["item_id"],
                title=item["title"],
                required=item["required"],
                status="missing",
                acceptance="required" if item["required"] else "optional",
                cta_action="request_upload",
            )
            self.db.add(checklist_item)

        self.db.commit()
        self.db.refresh(client)

        quarter_num = (period_start.month - 1) // 3 + 1
        vat_period_label = f"Q{quarter_num} {period_start.year}"

        onboarding_link = f"/onboard/{client.id}"

        # Send welcome email asynchronously
        try:
            from app.services.email_notification_service import EmailNotificationService
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
                "vat_period": vat_period_label,
            },
            "onboarding_link": onboarding_link,
        }

    def _tool_update_checklist_item(self, item_id: int, status: str) -> dict[str, Any]:
        """Update a checklist item status."""
        item = self.db.get(ChecklistItem, item_id)
        if not item:
            return {"error": f"Checklist item {item_id} not found"}

        valid_statuses = ["missing", "uploaded", "unknown"]
        if status not in valid_statuses:
            return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"}

        item.status = status
        self.db.commit()

        return {
            "success": True,
            "message": f"Checklist item '{item.title}' updated to '{status}'",
            "item": {
                "id": item.id,
                "title": item.title,
                "status": item.status,
            },
        }

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
        from app.services.email_service import EmailService

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
