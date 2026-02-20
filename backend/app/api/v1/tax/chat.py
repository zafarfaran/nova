"""Tax chat endpoint — AI streaming responses and conversation CRUD.

Adapted from Helio's chat router (helio/apps/api/app/routers/chat.py).
Changes from Helio original:
  - async -> sync (Nova uses synchronous SQLAlchemy)
  - AsyncSession -> Session from sqlalchemy.orm
  - get_db_session -> get_db from app.core.database
  - structlog -> stdlib logging
  - ChatService import from app.services.tax.chat
  - Tags prefixed with 'tax-'
  - async generators -> sync generators
"""

import json
import logging
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.tax.chat import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tax-chat"])


# ─── Pydantic request/response models ────────────────────────────────────


class ChatStreamRequest(BaseModel):
    conversation_id: str | None = None
    client_id: str
    message: str
    tax_plan_mode: bool = False
    context_snippet_ids: list[str] | None = None


class CreateConversationRequest(BaseModel):
    client_id: str
    title: str | None = None


class UpdateConversationRequest(BaseModel):
    title: str | None = None
    status: str | None = None


# ─── Endpoints ────────────────────────────────────────────────────────────


@router.post("/chat/stream")
def chat_stream(
    body: ChatStreamRequest,
    session: Session = Depends(get_db),
):
    """SSE streaming endpoint for AI chat responses."""
    user_id = "demo-user"

    logger.info(
        "Chat stream request, user_id=%s, client_id=%s, conversation_id=%s, message_length=%d",
        user_id,
        body.client_id,
        body.conversation_id,
        len(body.message),
    )

    service = ChatService(session)

    def event_generator():
        for event in service.stream_message(
            conversation_id=body.conversation_id,
            user_id=user_id,
            client_id=body.client_id,
            content=body.message,
            tax_plan_mode=body.tax_plan_mode,
            context_snippet_ids=body.context_snippet_ids,
        ):
            data = json.dumps(asdict(event))
            yield f"event: {event.type}\ndata: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/conversations")
def list_conversations(
    client_id: str | None = None,
    session: Session = Depends(get_db),
):
    """List conversations, optionally filtered by client_id."""
    user_id = "demo-user"

    logger.info(
        "Listing conversations, user_id=%s, client_id=%s",
        user_id,
        client_id,
    )

    service = ChatService(session)
    conversations = service.list_conversations(
        user_id=user_id,
        client_id=client_id,
    )

    return {
        "conversations": [
            {
                "id": c.id,
                "client_id": c.client_id,
                "title": c.title,
                "status": c.status,
                "last_message_preview": c.last_message_preview,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "message_count": c.message_count,
                "unread": c.unread,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in conversations
        ]
    }


@router.post("/chat/conversations")
def create_conversation(
    body: CreateConversationRequest,
    session: Session = Depends(get_db),
):
    """Create a new conversation."""
    user_id = "demo-user"

    logger.info(
        "Creating conversation, user_id=%s, client_id=%s, title=%s",
        user_id,
        body.client_id,
        body.title,
    )

    service = ChatService(session)
    conversation = service.create_conversation(
        user_id=user_id,
        client_id=body.client_id,
        title=body.title,
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "client_id": conversation.client_id,
    }


@router.get("/chat/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    session: Session = Depends(get_db),
):
    """Get messages for a conversation."""
    logger.info("Fetching messages, conversation_id=%s", conversation_id)

    service = ChatService(session)
    messages = service.get_messages(conversation_id)

    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "insights": m.insights,
                "dashboard_data": m.dashboard_data,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
    }


@router.patch("/chat/conversations/{conversation_id}")
def update_conversation(
    conversation_id: str,
    body: UpdateConversationRequest,
    session: Session = Depends(get_db),
):
    """Update a conversation's title or status."""
    logger.info(
        "Updating conversation, conversation_id=%s, title=%s, status=%s",
        conversation_id,
        body.title,
        body.status,
    )

    # Filter out None values so we only update provided fields
    updates = {k: v for k, v in body.model_dump().items() if v is not None}

    if updates:
        service = ChatService(session)
        service.update_conversation(conversation_id, **updates)

    return {"ok": True}


@router.delete("/chat/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    session: Session = Depends(get_db),
):
    """Soft-delete a conversation."""
    logger.info("Deleting conversation, conversation_id=%s", conversation_id)

    service = ChatService(session)
    service.delete_conversation(conversation_id)

    return {"ok": True}
