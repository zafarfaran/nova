"""Service layer for Chat operations with AI function calling."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.tools import TOOL_DEFINITIONS, ChatTools
from app.config import get_settings
from app.models.chat import ChatMessage, ChatSession, MessageRole

SYSTEM_PROMPT = """You are Nova, an AI assistant for UK VAT compliance. You help accountants manage VAT evidence collection for their clients.

You have access to tools to:
- List all clients and search for specific clients
- Get detailed client information including document status and bank connections
- View and update document checklists
- Find clients who need attention (missing documents)
- Create new clients

Always be helpful, concise, and professional. When showing data, format it clearly.
If asked about a specific client, use the tools to fetch real data.

## Creating Clients
When a user wants to create a new client, you need at minimum:
1. **Client Name** (required) - The business/client name
2. **Email** (required) - Primary email address for the client

Optionally gather:
3. **Entity Type** - sole_trader, partnership, llp, limited_company, plc, charity, or other
4. **VAT Scheme** - standard, flat_rate, cash_accounting, or annual_accounting
5. **VAT Period** - Start and end dates if known

If the user only provides a name, ask for their email address before creating the client.
Once you have name and email, you can create the client - other fields have sensible defaults.

Important: Always use the tools to get real data - never make up information.
Important: Clients created here will appear on the main dashboard immediately."""


class ChatService:
    """Service for AI chat with function calling."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.tools = ChatTools(db)

    def create_session(self, client_id: int | None = None, title: str | None = None) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(client_id=client_id, title=title or "New Chat")
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int) -> ChatSession | None:
        """Get a chat session."""
        return self.db.get(ChatSession, session_id)

    def list_sessions(self, limit: int = 20) -> list[ChatSession]:
        """List recent chat sessions."""
        stmt = select(ChatSession).order_by(ChatSession.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_messages(self, session_id: int) -> list[ChatMessage]:
        """Get all messages in a session."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def _save_message(
        self,
        session_id: int,
        role: MessageRole,
        content: str,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> ChatMessage:
        """Save a message to the session."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def _build_messages(self, session_id: int) -> list[dict]:
        """Build message history for OpenAI API call."""
        messages = self.get_messages(session_id)
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in messages:
            if msg.role == MessageRole.USER:
                api_messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                assistant_msg = {"role": "assistant", "content": msg.content or ""}
                if msg.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["input"]),
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                api_messages.append(assistant_msg)
            elif msg.role == MessageRole.TOOL:
                api_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content,
                })

        return api_messages

    def _convert_tools_for_openai(self) -> list[dict]:
        """Convert tool definitions to OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for tool in TOOL_DEFINITIONS
        ]

    async def chat(self, session_id: int, user_message: str) -> str:
        """Process a chat message and return the response."""
        # Save user message
        self._save_message(session_id, MessageRole.USER, user_message)

        # Build conversation history
        messages = self._build_messages(session_id)

        # Call OpenAI with tools
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=self._convert_tools_for_openai(),
            tool_choice="auto",
        )

        # Process response - handle tool calls in a loop
        while response.choices[0].finish_reason == "tool_calls":
            assistant_message = response.choices[0].message
            assistant_text = assistant_message.content or ""
            tool_calls = []

            for tc in assistant_message.tool_calls or []:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": json.loads(tc.function.arguments),
                })

            # Save assistant message with tool calls
            self._save_message(
                session_id,
                MessageRole.ASSISTANT,
                assistant_text,
                tool_calls=tool_calls,
            )

            # Execute tools and save results
            for tc in tool_calls:
                result = self.tools.execute(tc["name"], tc["input"])
                result_str = json.dumps(result, indent=2, default=str)

                self._save_message(
                    session_id,
                    MessageRole.TOOL,
                    result_str,
                    tool_call_id=tc["id"],
                )

            # Continue conversation with tool results
            messages = self._build_messages(session_id)
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self._convert_tools_for_openai(),
                tool_choice="auto",
            )

        # Extract final text response
        final_text = response.choices[0].message.content or ""

        # Save final assistant message
        self._save_message(session_id, MessageRole.ASSISTANT, final_text)

        return final_text

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Process chat with streaming response (stateless - no session persistence).

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Yields:
            SSE formatted strings with JSON data
        """
        # Build API messages with system prompt
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Call OpenAI with tools (streaming)
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            tools=self._convert_tools_for_openai(),
            tool_choice="auto",
            stream=True,
        )

        # Collect streamed response
        collected_text = ""
        tool_calls_data: dict[int, dict] = {}  # index -> {id, name, arguments}
        finish_reason = None

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            finish_reason = chunk.choices[0].finish_reason if chunk.choices else None

            if delta:
                # Stream text content
                if delta.content:
                    collected_text += delta.content
                    yield f"data: {json.dumps({'type': 'text', 'content': delta.content})}\n\n"

                # Collect tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_data:
                            tool_calls_data[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc.id:
                            tool_calls_data[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_data[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_data[idx]["arguments"] += tc.function.arguments

        # Handle tool calls if any
        while finish_reason == "tool_calls" and tool_calls_data:
            # Process each tool call
            tool_results = []
            for idx in sorted(tool_calls_data.keys()):
                tc = tool_calls_data[idx]
                tool_name = tc["name"]

                # Notify frontend about tool execution
                yield f"data: {json.dumps({'type': 'tool_executing', 'tool': tool_name})}\n\n"

                try:
                    tool_input = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    result = self.tools.execute(tool_name, tool_input)
                    result_str = json.dumps(result, indent=2, default=str)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})

                tool_results.append({
                    "tool_call_id": tc["id"],
                    "role": "tool",
                    "content": result_str,
                })

                yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name})}\n\n"

            # Build messages with tool results for continuation
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": collected_text or None}
            assistant_msg["tool_calls"] = [
                {
                    "id": tool_calls_data[idx]["id"],
                    "type": "function",
                    "function": {
                        "name": tool_calls_data[idx]["name"],
                        "arguments": tool_calls_data[idx]["arguments"],
                    },
                }
                for idx in sorted(tool_calls_data.keys())
            ]

            continuation_messages = api_messages + [assistant_msg] + tool_results

            # Continue with tool results (streaming)
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=continuation_messages,
                tools=self._convert_tools_for_openai(),
                tool_choice="auto",
                stream=True,
            )

            # Reset for next iteration
            collected_text = ""
            tool_calls_data = {}
            finish_reason = None

            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                finish_reason = chunk.choices[0].finish_reason if chunk.choices else None

                if delta:
                    if delta.content:
                        collected_text += delta.content
                        yield f"data: {json.dumps({'type': 'text', 'content': delta.content})}\n\n"

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_data:
                                tool_calls_data[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc.id:
                                tool_calls_data[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_data[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls_data[idx]["arguments"] += tc.function.arguments

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
