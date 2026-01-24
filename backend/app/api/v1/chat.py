"""Chat API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from app.services.chat_service import ChatService


class ChatStreamMessage(BaseModel):
    """A single message in the chat stream request."""

    role: str
    content: str


class ChatStreamRequest(BaseModel):
    """Request schema for streaming chat."""

    messages: list[ChatStreamMessage]

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    data: ChatSessionCreate,
    db: Session = Depends(get_db),
) -> ChatSessionResponse:
    """Create a new chat session."""
    service = ChatService(db)
    session = service.create_session(client_id=data.client_id, title=data.title)
    return ChatSessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[ChatSessionResponse]:
    """List recent chat sessions."""
    service = ChatService(db)
    sessions = service.list_sessions(limit=limit)
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> ChatSessionResponse:
    """Get a chat session."""
    service = ChatService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ChatSessionResponse.model_validate(session)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
) -> list[ChatMessageResponse]:
    """Get all messages in a session."""
    service = ChatService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = service.get_messages(session_id)
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(
    session_id: int,
    data: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Send a message and get AI response."""
    service = ChatService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    response_text = await service.chat(session_id, data.message)
    messages = service.get_messages(session_id)

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
    )


@router.post("/stream")
async def chat_stream(
    data: ChatStreamRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream a chat response (stateless - no session persistence).

    This endpoint accepts conversation history and returns a streaming SSE response.
    Used by the frontend accountant AI chat.
    """
    service = ChatService(db)
    messages = [{"role": m.role, "content": m.content} for m in data.messages]

    return StreamingResponse(
        service.chat_stream(messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
