"""AI tools/functions for the chat interface - using Prisma schema."""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.client_setup import ClientSetup, ChecklistItem, BankConnection, generate_cuid


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
                    "type": "string",
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
                    "type": "string",
                    "description": "The ID of the client",
                },
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "get_clients_needing_attention",
        "description": "Get a list of clients who have missing documents or need follow-up",
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
                "vat_period_start": {
                    "type": "string",
                    "description": "Start date of current VAT period (YYYY-MM-DD format)",
                },
                "vat_period_end": {
                    "type": "string",
                    "description": "End date of current VAT period (YYYY-MM-DD format)",
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
                    "type": "string",
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
]


class ChatTools:
    """Executor for chat tools using Prisma schema."""

    def __init__(self, db: Session):
        self.db = db

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return the result."""
        method = getattr(self, f"_tool_{tool_name}", None)
        if not method:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return method(**arguments)
        except Exception as e:
            return {"error": str(e)}

    def _tool_list_clients(self) -> dict[str, Any]:
        """List all clients."""
        clients = list(self.db.query(ClientSetup).order_by(ClientSetup.updatedAt.desc()).all())
        return {
            "clients": [
                {
                    "id": c.id,
                    "name": c.clientName,
                    "email": c.email,
                    "entity_type": c.entityType,
                    "vat_scheme": c.vatScheme,
                    "vat_period": c.vatPeriodLabel,
                }
                for c in clients
            ],
            "total": len(clients),
        }

    def _tool_get_client_details(self, client_id: str) -> dict[str, Any]:
        """Get detailed client information."""
        client = self.db.get(ClientSetup, client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        # Get checklist summary
        checklist_items = list(
            self.db.query(ChecklistItem)
            .filter(ChecklistItem.clientSetupId == client_id)
            .all()
        )
        required_items = [i for i in checklist_items if i.required]
        uploaded_items = [i for i in required_items if i.status == "uploaded"]

        # Get bank connections
        bank_connections = list(
            self.db.query(BankConnection)
            .filter(BankConnection.clientSetupId == client_id, BankConnection.isActive == True)
            .all()
        )

        return {
            "client": {
                "id": client.id,
                "name": client.clientName,
                "email": client.email,
                "entity_type": client.entityType,
                "vat_scheme": client.vatScheme,
                "vat_period": {
                    "label": client.vatPeriodLabel,
                    "start": client.vatPeriodStart.isoformat() if client.vatPeriodStart else None,
                    "end": client.vatPeriodEnd.isoformat() if client.vatPeriodEnd else None,
                },
                "notes": client.notes,
                "created_at": client.createdAt.isoformat() if client.createdAt else None,
            },
            "documents": {
                "total_required": len(required_items),
                "uploaded": len(uploaded_items),
                "missing": len(required_items) - len(uploaded_items),
                "completion_percentage": round(len(uploaded_items) / len(required_items) * 100) if required_items else 100,
            },
            "bank_connections": [
                {
                    "institution": bc.institutionName,
                    "account_name": bc.accountName,
                    "account_type": bc.accountType,
                }
                for bc in bank_connections
            ],
            "has_bank_connected": len(bank_connections) > 0,
        }

    def _tool_search_clients(self, query: str) -> dict[str, Any]:
        """Search clients by name or email."""
        query_lower = query.lower()
        clients = list(
            self.db.query(ClientSetup)
            .filter(
                (ClientSetup.clientName.ilike(f"%{query_lower}%")) |
                (ClientSetup.email.ilike(f"%{query_lower}%"))
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
                    "name": c.clientName,
                    "email": c.email,
                    "entity_type": c.entityType,
                    "vat_scheme": c.vatScheme,
                }
                for c in clients
            ],
            "total": len(clients),
        }

    def _tool_get_document_checklist(self, client_id: str) -> dict[str, Any]:
        """Get document checklist for a client."""
        client = self.db.get(ClientSetup, client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        checklist_items = list(
            self.db.query(ChecklistItem)
            .filter(ChecklistItem.clientSetupId == client_id)
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
                "has_file": item.uploadedFileUrl is not None,
            })

        required = [i for i in items if i["required"]]
        uploaded = [i for i in required if i["status"] == "uploaded"]

        return {
            "client_name": client.clientName,
            "checklist": items,
            "summary": {
                "total_items": len(items),
                "required_items": len(required),
                "uploaded": len(uploaded),
                "missing": len(required) - len(uploaded),
                "completion_percentage": round(len(uploaded) / len(required) * 100) if required else 100,
            },
        }

    def _tool_get_clients_needing_attention(self) -> dict[str, Any]:
        """Get clients with missing documents."""
        clients = list(self.db.query(ClientSetup).all())

        needs_attention = []
        for client in clients:
            checklist_items = list(
                self.db.query(ChecklistItem)
                .filter(
                    ChecklistItem.clientSetupId == client.id,
                    ChecklistItem.required == True,
                    ChecklistItem.status != "uploaded"
                )
                .all()
            )

            if checklist_items:
                needs_attention.append({
                    "id": client.id,
                    "name": client.clientName,
                    "email": client.email,
                    "missing_documents": len(checklist_items),
                    "missing_items": [item.title for item in checklist_items[:3]],  # Show first 3
                })

        return {
            "clients_needing_attention": needs_attention,
            "total": len(needs_attention),
            "message": f"{len(needs_attention)} client(s) have missing documents" if needs_attention else "All clients are up to date!",
        }

    def _tool_create_client(
        self,
        client_name: str,
        email: str,
        entity_type: str = "limited_company",
        vat_scheme: str = "standard",
        vat_period_start: str | None = None,
        vat_period_end: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a new client."""
        # Check if client with same email already exists
        existing = self.db.query(ClientSetup).filter(ClientSetup.email == email).first()
        if existing:
            return {
                "error": f"A client with email '{email}' already exists",
                "existing_client": {
                    "id": existing.id,
                    "name": existing.clientName,
                    "email": existing.email,
                },
            }

        # Parse dates or use defaults (current quarter)
        now = datetime.now()
        if vat_period_start:
            try:
                period_start = datetime.fromisoformat(vat_period_start)
            except ValueError:
                return {"error": f"Invalid date format for vat_period_start: {vat_period_start}. Use YYYY-MM-DD."}
        else:
            # Default to start of current quarter
            quarter_month = ((now.month - 1) // 3) * 3 + 1
            period_start = datetime(now.year, quarter_month, 1)

        if vat_period_end:
            try:
                period_end = datetime.fromisoformat(vat_period_end)
            except ValueError:
                return {"error": f"Invalid date format for vat_period_end: {vat_period_end}. Use YYYY-MM-DD."}
        else:
            # Default to end of current quarter
            quarter_end_month = ((now.month - 1) // 3) * 3 + 3
            if quarter_end_month == 3:
                period_end = datetime(now.year, 3, 31)
            elif quarter_end_month == 6:
                period_end = datetime(now.year, 6, 30)
            elif quarter_end_month == 9:
                period_end = datetime(now.year, 9, 30)
            else:
                period_end = datetime(now.year, 12, 31)

        # Generate VAT period label
        quarter_num = (period_start.month - 1) // 3 + 1
        vat_period_label = f"Q{quarter_num} {period_start.year}"

        # Create the client
        client_id = generate_cuid()
        client = ClientSetup(
            id=client_id,
            email=email,
            clientName=client_name,
            entityType=entity_type,
            vatScheme=vat_scheme,
            vatPeriodStart=period_start,
            vatPeriodEnd=period_end,
            vatPeriodLabel=vat_period_label,
            bankAccounts=[],
            salesChannels=[],
            notes=notes,
        )
        self.db.add(client)

        # Create default checklist items
        default_checklist = [
            {"itemId": "bank_statements", "title": "Bank Statements", "required": True},
            {"itemId": "sales_invoices", "title": "Sales Invoices", "required": True},
            {"itemId": "purchase_invoices", "title": "Purchase Invoices", "required": True},
            {"itemId": "expense_receipts", "title": "Expense Receipts", "required": True},
            {"itemId": "payroll_records", "title": "Payroll Records", "required": False},
        ]

        for item in default_checklist:
            checklist_item = ChecklistItem(
                id=generate_cuid(),
                clientSetupId=client_id,
                itemId=item["itemId"],
                title=item["title"],
                required=item["required"],
                status="missing",
                acceptance="required" if item["required"] else "optional",
                ctaAction="request_upload",
            )
            self.db.add(checklist_item)

        self.db.commit()
        self.db.refresh(client)

        return {
            "success": True,
            "message": f"Client '{client_name}' created successfully",
            "client": {
                "id": client.id,
                "name": client.clientName,
                "email": client.email,
                "entity_type": client.entityType,
                "vat_scheme": client.vatScheme,
                "vat_period": vat_period_label,
            },
            "onboarding_link": f"/onboard/{client.id}",
        }

    def _tool_update_checklist_item(self, item_id: str, status: str) -> dict[str, Any]:
        """Update a checklist item status."""
        item = self.db.get(ChecklistItem, item_id)
        if not item:
            return {"error": f"Checklist item {item_id} not found"}

        valid_statuses = ["missing", "uploaded", "unknown"]
        if status not in valid_statuses:
            return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"}

        item.status = status
        item.updatedAt = datetime.now()
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
