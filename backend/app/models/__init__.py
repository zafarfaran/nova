"""SQLAlchemy models package."""

from app.models.base import Base, TimestampMixin

# Core models
from app.models.client import Client, EntityType, ClientType
from app.models.document import Document, DocumentStatus
from app.models.validation import ValidationResult, RuleType, ValidationStatus
from app.models.chaser import ChaserRequest, ChaserResponse, ChaserStatus
from app.models.chat import ChatSession, ChatMessage, MessageRole

# Enterprise schema models
from app.models.client_contact import ClientContact
from app.models.engagement import Engagement, EngagementType, EngagementStatus
from app.models.document_type import DocumentCategory, DocumentType
from app.models.file_object import FileObject
from app.models.document_version import DocumentVersion, ExtractionStatus
from app.models.counterparty import Counterparty, CounterpartyType
from app.models.financial_account import FinancialAccount, AccountType
from app.models.request_set import RequestSet, RequestSetStatus
from app.models.request_item import RequestItem, RequestItemStatus, request_item_documents
from app.models.request_template import RequestTemplate, RequestTemplateItem
from app.models.audit_log import AuditLog

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Core models
    "Client",
    "EntityType",
    "ClientType",
    "Document",
    "DocumentStatus",
    "ValidationResult",
    "RuleType",
    "ValidationStatus",
    "ChaserRequest",
    "ChaserResponse",
    "ChaserStatus",
    "ChatSession",
    "ChatMessage",
    "MessageRole",
    # Enterprise schema models
    "ClientContact",
    "Engagement",
    "EngagementType",
    "EngagementStatus",
    "DocumentCategory",
    "DocumentType",
    "FileObject",
    "DocumentVersion",
    "ExtractionStatus",
    "Counterparty",
    "CounterpartyType",
    "FinancialAccount",
    "AccountType",
    "RequestSet",
    "RequestSetStatus",
    "RequestItem",
    "RequestItemStatus",
    "request_item_documents",
    "RequestTemplate",
    "RequestTemplateItem",
    "AuditLog",
]
