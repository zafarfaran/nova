"""Pydantic schemas for Chat."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.chat import MessageRole


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""

    client_id: int | None = None
    title: str | None = None


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int | None
    title: str | None
    created_at: datetime


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: MessageRole
    content: str
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    created_at: datetime


class ChatRequest(BaseModel):
    """Schema for sending a chat message."""

    message: str


class ChatResponse(BaseModel):
    """Schema for chat response."""

    session_id: int
    response: str
    messages: list[ChatMessageResponse]
