"""Pydantic schemas package."""

# Import all schemas from domain modules
from app.schemas.clients import (
    ClientBase,
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientList,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
)
from app.schemas.documents import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    ExtractedData,
    DocumentResponse,
    DocumentList,
    DocumentUploadResponse,
    PresignedUrlResponse,
)
from app.schemas.engagements import (
    EngagementBase,
    EngagementCreate,
    EngagementUpdate,
    EngagementResponse,
    EngagementList,
)
from app.schemas.requests import (
    RequestSetBase,
    RequestSetCreate,
    RequestSetUpdate,
    RequestSetResponse,
    RequestSetList,
    RequestItemBase,
    RequestItemCreate,
    RequestItemUpdate,
    RequestItemResponse,
    RequestItemList,
)
from app.schemas.validation import (
    ValidationResultBase,
    ValidationResultResponse,
    ValidationResultList,
    ValidationSummary,
    ValidationRunResponse,
)
from app.schemas.chaser import (
    ChaserRequestCreate,
    ChaserRequestResponse,
    ChaserRequestList,
    AutoChaseRequest,
    ChaserResponseCreate,
    ChaserResponseResponse,
)
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
)
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogList,
)
from app.schemas.email import (
    EmailPurpose,
    EmailTone,
    EmailRequest,
    AIEmailGenerationRequest,
    EmailResponse,
)

__all__ = [
    # Clients
    "ClientBase",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ClientList",
    "OnboardingCompleteRequest",
    "OnboardingCompleteResponse",
    # Documents
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "ExtractedData",
    "DocumentResponse",
    "DocumentList",
    "DocumentUploadResponse",
    "PresignedUrlResponse",
    # Engagements
    "EngagementBase",
    "EngagementCreate",
    "EngagementUpdate",
    "EngagementResponse",
    "EngagementList",
    # Requests
    "RequestSetBase",
    "RequestSetCreate",
    "RequestSetUpdate",
    "RequestSetResponse",
    "RequestSetList",
    "RequestItemBase",
    "RequestItemCreate",
    "RequestItemUpdate",
    "RequestItemResponse",
    "RequestItemList",
    # Validation
    "ValidationResultBase",
    "ValidationResultResponse",
    "ValidationResultList",
    "ValidationSummary",
    "ValidationRunResponse",
    # Chaser
    "ChaserRequestCreate",
    "ChaserRequestResponse",
    "ChaserRequestList",
    "AutoChaseRequest",
    "ChaserResponseCreate",
    "ChaserResponseResponse",
    # Chat
    "ChatSessionCreate",
    "ChatSessionResponse",
    "ChatMessageResponse",
    "ChatRequest",
    "ChatResponse",
    # Audit
    "AuditLogResponse",
    "AuditLogList",
    # Email
    "EmailPurpose",
    "EmailTone",
    "EmailRequest",
    "AIEmailGenerationRequest",
    "EmailResponse",
]
