"""SQLAlchemy models package."""

from app.models.shared import Base, TimestampMixin

# Core models
from app.models.clients import Client, EntityType, ClientType
from app.models.documents import Document, DocumentStatus
from app.models.validation import ValidationResult, RuleType, ValidationStatus
from app.models.chaser import ChaserRequest, ChaserResponse, ChaserStatus
from app.models.chat import ChatSession, ChatMessage, MessageRole

# Enterprise schema models
from app.models.clients import ClientContact
from app.models.engagements import Engagement, EngagementType, EngagementStatus
from app.models.documents import DocumentCategory, DocumentType
from app.models.documents import FileObject
from app.models.documents import DocumentVersion, ExtractionStatus
from app.models.clients import Counterparty, CounterpartyType
from app.models.clients import FinancialAccount, AccountType
from app.models.requests import RequestSet, RequestSetStatus
from app.models.requests import RequestItem, RequestItemStatus, request_item_documents
from app.models.requests import RequestTemplate, RequestTemplateItem
from app.models.audit import AuditLog

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
