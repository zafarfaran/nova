"""AI tools/functions for the chat interface."""

from typing import Any

from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.document import Document, DocumentStatus
from app.models.evidence import EvidenceItem
from app.models.vat_period import VATPeriod
from app.services.chaser_service import ChaserService
from app.services.evidence_service import EvidenceService
from app.services.validation_service import ValidationService

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
        "name": "get_client_status",
        "description": "Get the current status of a specific client including their VAT periods and overall progress",
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
        "name": "get_vat_period_status",
        "description": "Get detailed status of a VAT period including evidence coverage, gaps, and validation summary",
        "parameters": {
            "type": "object",
            "properties": {
                "period_id": {
                    "type": "integer",
                    "description": "The ID of the VAT period",
                },
            },
            "required": ["period_id"],
        },
    },
    {
        "name": "generate_document_checklist",
        "description": "Generate a checklist of required documents for a VAT period, showing what's received and what's missing",
        "parameters": {
            "type": "object",
            "properties": {
                "period_id": {
                    "type": "integer",
                    "description": "The ID of the VAT period",
                },
            },
            "required": ["period_id"],
        },
    },
    {
        "name": "get_missing_documents",
        "description": "Get a list of missing documents/evidence for a VAT period",
        "parameters": {
            "type": "object",
            "properties": {
                "period_id": {
                    "type": "integer",
                    "description": "The ID of the VAT period",
                },
            },
            "required": ["period_id"],
        },
    },
    {
        "name": "get_validation_issues",
        "description": "Get all validation issues/failures for a VAT period",
        "parameters": {
            "type": "object",
            "properties": {
                "period_id": {
                    "type": "integer",
                    "description": "The ID of the VAT period",
                },
            },
            "required": ["period_id"],
        },
    },
    {
        "name": "create_chaser_request",
        "description": "Create a chaser request to ask for missing documents from a client",
        "parameters": {
            "type": "object",
            "properties": {
                "period_id": {
                    "type": "integer",
                    "description": "The ID of the VAT period",
                },
                "recipient_email": {
                    "type": "string",
                    "description": "Email address to send the chaser to",
                },
            },
            "required": ["period_id", "recipient_email"],
        },
    },
    {
        "name": "get_recent_uploads",
        "description": "Get recently uploaded documents for a VAT period",
        "parameters": {
            "type": "object",
            "properties": {
                "period_id": {
                    "type": "integer",
                    "description": "The ID of the VAT period",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of documents to return (default 10)",
                },
            },
            "required": ["period_id"],
        },
    },
    {
        "name": "create_client",
        "description": "Create a new client in the system. Requires at minimum the client name. Before calling this tool, ensure you have gathered all available information from the user. If the user hasn't provided key details like VAT number, entity type, or contact email, ask them first before creating the client.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the client/business (required)",
                },
                "vat_number": {
                    "type": "string",
                    "description": "The client's VAT registration number (e.g., GB123456789)",
                },
                "entity_type": {
                    "type": "string",
                    "enum": ["sole_trader", "partnership", "llp", "limited_company", "plc", "charity", "other"],
                    "description": "The type of business entity. Options: sole_trader, partnership, llp, limited_company, plc, charity, other",
                },
                "contact_email": {
                    "type": "string",
                    "description": "Primary contact email address for the client",
                },
                "contact_name": {
                    "type": "string",
                    "description": "Name of the primary contact person",
                },
                "address": {
                    "type": "string",
                    "description": "Business address",
                },
                "notes": {
                    "type": "string",
                    "description": "Any additional notes about the client",
                },
            },
            "required": ["name"],
        },
    },
]


class ChatTools:
    """Executor for chat tools."""

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
        clients = list(self.db.query(Client).all())
        return {
            "clients": [
                {
                    "id": c.id,
                    "name": c.name,
                    "vat_number": c.vat_number,
                    "entity_type": c.entity_type.value,
                    "contact_email": c.contact_email,
                }
                for c in clients
            ],
            "total": len(clients),
        }

    def _tool_get_client_status(self, client_id: int) -> dict[str, Any]:
        """Get client status with VAT periods."""
        client = self.db.get(Client, client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        periods = list(
            self.db.query(VATPeriod).filter(VATPeriod.client_id == client_id).all()
        )

        period_summaries = []
        for period in periods:
            evidence_service = EvidenceService(self.db)
            coverage = evidence_service.get_coverage(period.id)
            period_summaries.append({
                "id": period.id,
                "period": f"{period.period_start} to {period.period_end}",
                "status": period.status.value,
                "coverage_percentage": coverage.overall_coverage_percentage,
                "is_complete": coverage.is_complete,
            })

        return {
            "client": {
                "id": client.id,
                "name": client.name,
                "vat_number": client.vat_number,
            },
            "vat_periods": period_summaries,
            "total_periods": len(periods),
        }

    def _tool_get_vat_period_status(self, period_id: int) -> dict[str, Any]:
        """Get detailed VAT period status."""
        period = self.db.get(VATPeriod, period_id)
        if not period:
            return {"error": f"VAT period {period_id} not found"}

        client = self.db.get(Client, period.client_id)
        evidence_service = EvidenceService(self.db)
        validation_service = ValidationService(self.db)

        coverage = evidence_service.get_coverage(period_id)
        gaps = evidence_service.get_gaps(period_id)
        validation_summary = validation_service.get_validation_summary(period_id)

        return {
            "period": {
                "id": period.id,
                "client_name": client.name if client else "Unknown",
                "start": str(period.period_start),
                "end": str(period.period_end),
                "status": period.status.value,
                "is_locked": period.is_locked,
            },
            "coverage": {
                "overall_percentage": coverage.overall_coverage_percentage,
                "total_expected": coverage.total_expected,
                "total_received": coverage.total_received,
                "is_complete": coverage.is_complete,
            },
            "gaps": {
                "total_missing": gaps.total_missing,
                "gap_count": len(gaps.gaps),
            },
            "validation": {
                "total_documents": validation_summary["total_documents"],
                "validated": validation_summary["validated_documents"],
                "failed": validation_summary["failed_documents"],
                "pending": validation_summary["pending_documents"],
            },
        }

    def _tool_generate_document_checklist(self, period_id: int) -> dict[str, Any]:
        """Generate document checklist."""
        period = self.db.get(VATPeriod, period_id)
        if not period:
            return {"error": f"VAT period {period_id} not found"}

        evidence_items = list(
            self.db.query(EvidenceItem)
            .filter(EvidenceItem.vat_period_id == period_id)
            .all()
        )

        checklist = []
        for item in evidence_items:
            status_icon = "✅" if item.is_complete else ("🔶" if item.received_count > 0 else "❌")
            checklist.append({
                "category": item.category.value.replace("_", " ").title(),
                "status": status_icon,
                "expected": item.expected_count,
                "received": item.received_count,
                "missing": max(0, item.expected_count - item.received_count),
                "coverage": f"{item.coverage_percentage:.0f}%",
            })

        return {
            "period": f"{period.period_start} to {period.period_end}",
            "checklist": checklist,
            "summary": {
                "total_categories": len(checklist),
                "complete": sum(1 for c in checklist if c["status"] == "✅"),
                "partial": sum(1 for c in checklist if c["status"] == "🔶"),
                "missing": sum(1 for c in checklist if c["status"] == "❌"),
            },
        }

    def _tool_get_missing_documents(self, period_id: int) -> dict[str, Any]:
        """Get missing documents."""
        evidence_service = EvidenceService(self.db)
        gaps = evidence_service.get_gaps(period_id)

        return {
            "period_id": period_id,
            "missing_items": [
                {
                    "category": gap.category.value.replace("_", " ").title(),
                    "missing_count": gap.missing_count,
                    "description": gap.description,
                }
                for gap in gaps.gaps
            ],
            "total_missing": gaps.total_missing,
        }

    def _tool_get_validation_issues(self, period_id: int) -> dict[str, Any]:
        """Get validation issues."""
        from sqlalchemy import select
        from app.models.validation import ValidationResult, ValidationStatus

        # Get all failed/warning validations for the period
        stmt = (
            select(ValidationResult)
            .join(Document)
            .join(EvidenceItem)
            .where(
                EvidenceItem.vat_period_id == period_id,
                ValidationResult.status.in_([ValidationStatus.FAILED, ValidationStatus.WARNING]),
            )
        )
        issues = list(self.db.scalars(stmt).all())

        return {
            "period_id": period_id,
            "issues": [
                {
                    "document_id": issue.document_id,
                    "rule": issue.rule_type.value,
                    "status": issue.status.value,
                    "message": issue.message,
                }
                for issue in issues
            ],
            "total_issues": len(issues),
        }

    def _tool_create_chaser_request(
        self, period_id: int, recipient_email: str
    ) -> dict[str, Any]:
        """Create a chaser request."""
        chaser_service = ChaserService(self.db)
        chaser = chaser_service.auto_chase(period_id, recipient_email)

        if not chaser:
            return {"message": "No gaps found - nothing to chase!"}

        return {
            "chaser_id": chaser.id,
            "recipient": chaser.recipient_email,
            "items_requested": chaser.requested_items,
            "upload_token": chaser.upload_token,
            "message": f"Chaser created for {len(chaser.requested_items)} missing items",
        }

    def _tool_get_recent_uploads(
        self, period_id: int, limit: int = 10
    ) -> dict[str, Any]:
        """Get recent uploads."""
        from sqlalchemy import select

        stmt = (
            select(Document)
            .join(EvidenceItem)
            .where(EvidenceItem.vat_period_id == period_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        documents = list(self.db.scalars(stmt).all())

        return {
            "period_id": period_id,
            "recent_documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status.value,
                    "invoice_number": doc.invoice_number,
                    "supplier": doc.supplier_name,
                    "amount": str(doc.gross_amount) if doc.gross_amount else None,
                    "uploaded_at": doc.created_at.isoformat(),
                }
                for doc in documents
            ],
            "count": len(documents),
        }

    def _tool_create_client(
        self,
        name: str,
        vat_number: str | None = None,
        entity_type: str | None = None,
        contact_email: str | None = None,
        contact_name: str | None = None,
        address: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a new client."""
        from app.models.client import EntityType

        # Check if client with same name already exists
        existing = self.db.query(Client).filter(Client.name == name).first()
        if existing:
            return {
                "error": f"A client with the name '{name}' already exists (ID: {existing.id})",
                "existing_client": {
                    "id": existing.id,
                    "name": existing.name,
                    "vat_number": existing.vat_number,
                },
            }

        # Check if VAT number already exists (if provided)
        if vat_number:
            existing_vat = self.db.query(Client).filter(Client.vat_number == vat_number).first()
            if existing_vat:
                return {
                    "error": f"A client with VAT number '{vat_number}' already exists",
                    "existing_client": {
                        "id": existing_vat.id,
                        "name": existing_vat.name,
                        "vat_number": existing_vat.vat_number,
                    },
                }

        # Parse entity type
        parsed_entity_type = EntityType.LIMITED_COMPANY  # default
        if entity_type:
            try:
                parsed_entity_type = EntityType(entity_type.lower())
            except ValueError:
                return {
                    "error": f"Invalid entity type: '{entity_type}'. Valid options are: {', '.join(e.value for e in EntityType)}"
                }

        # Create the client
        client = Client(
            name=name,
            vat_number=vat_number,
            entity_type=parsed_entity_type,
            contact_email=contact_email,
            contact_name=contact_name,
            address=address,
            notes=notes,
        )
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)

        return {
            "success": True,
            "message": f"Client '{name}' created successfully",
            "client": {
                "id": client.id,
                "name": client.name,
                "vat_number": client.vat_number,
                "entity_type": client.entity_type.value,
                "contact_email": client.contact_email,
                "contact_name": client.contact_name,
                "address": client.address,
                "notes": client.notes,
            },
        }
