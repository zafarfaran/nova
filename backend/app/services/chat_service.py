"""Service layer for Chat operations with AI function calling."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import get_chat_provider
from app.ai.tools import TOOL_DEFINITIONS, ChatTools
from app.models.chat import ChatMessage, ChatSession, MessageRole

SYSTEM_PROMPT = """You are Nova, an AI assistant for UK VAT compliance. You help accountants manage VAT evidence collection for their clients.

You have access to tools to:
- List and check client status
- View VAT period progress and coverage
- Generate document checklists
- Find missing documents and validation issues
- Create chaser requests for missing evidence
- Create new clients

Always be helpful, concise, and professional. When showing data, format it clearly.
If asked about a specific client or period, use the tools to fetch real data.
When generating checklists, use the generate_document_checklist tool.

## Creating Clients
When a user wants to create a new client, gather the following information BEFORE calling the create_client tool:
1. **Name** (required) - The business/client name
2. **VAT Number** - The UK VAT registration number (format: GB followed by 9 digits, e.g., GB123456789)
3. **Entity Type** - Ask what type of business: sole trader, partnership, LLP, limited company, PLC, charity, or other
4. **Contact Email** - Primary email address for correspondence
5. **Contact Name** - Name of the main contact person

If the user only provides partial information, ask them for the missing key details before creating the client. For example:
- If they say "create a client called ABC Ltd", ask for their VAT number, entity type, and contact details.
- If they provide name and VAT number but no entity type, ask what type of business entity it is.

Only call the create_client tool once you have gathered sufficient information OR the user explicitly says they want to proceed without certain details.

Important: Always use the tools to get real data - never make up information."""


class ChatService:
    """Service for AI chat with function calling."""

    def __init__(self, db: Session):
        self.db = db
        self.chat_provider = get_chat_provider()
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
        """Build message history for AI API call."""
        messages = self.get_messages(session_id)
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in messages:
            if msg.role == MessageRole.USER:
                api_messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                assistant_msg = {"role": "assistant", "content": msg.content or ""}
                if msg.tool_calls:
                    # Store tool calls in OpenAI format for compatibility
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

    def _convert_tools_for_api(self) -> list[dict]:
        """Convert tool definitions to API format (OpenAI-style)."""
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

        # Call AI provider with tools
        response = await self.chat_provider.chat(
            messages=messages,
            tools=self._convert_tools_for_api(),
            tool_choice="auto",
        )

        # Process response - handle tool calls in a loop
        while response["finish_reason"] == "tool_calls" or (
            response["finish_reason"] == "tool_use" and response["tool_calls"]
        ):
            assistant_text = response["content"]
            tool_calls = response["tool_calls"]

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
            response = await self.chat_provider.chat(
                messages=messages,
                tools=self._convert_tools_for_api(),
                tool_choice="auto",
            )

        # Extract final text response
        final_text = response["content"]

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

        # Call AI provider with tools (streaming)
        collected_text = ""
        tool_calls_list = []
        finish_reason = None

        async for chunk in self.chat_provider.chat_stream(
            messages=api_messages,
            tools=self._convert_tools_for_api(),
            tool_choice="auto",
        ):
            if chunk["type"] == "text":
                collected_text += chunk["content"]
                yield f"data: {json.dumps({'type': 'text', 'content': chunk['content']})}\n\n"

            elif chunk["type"] == "tool_calls":
                tool_calls_list = chunk["tool_calls"]

            elif chunk["type"] == "done":
                finish_reason = chunk["finish_reason"]

        # Handle tool calls if any
        while finish_reason in ("tool_calls", "tool_use") and tool_calls_list:
            # Process each tool call
            tool_results = []
            for tc in tool_calls_list:
                tool_name = tc["name"]

                # Notify frontend about tool execution
                yield f"data: {json.dumps({'type': 'tool_executing', 'tool': tool_name})}\n\n"

                try:
                    # Handle both raw dict input and JSON string
                    if isinstance(tc.get("arguments"), str):
                        args_str = tc["arguments"].strip()
                        tool_input = json.loads(args_str) if args_str else {}
                    else:
                        tool_input = tc.get("input", {})

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
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc.get("arguments", json.dumps(tc.get("input", {}))),
                    },
                }
                for tc in tool_calls_list
            ]

            continuation_messages = api_messages + [assistant_msg] + tool_results

            # Reset for next iteration
            collected_text = ""
            tool_calls_list = []
            finish_reason = None

            # Continue with tool results (streaming)
            async for chunk in self.chat_provider.chat_stream(
                messages=continuation_messages,
                tools=self._convert_tools_for_api(),
                tool_choice="auto",
            ):
                if chunk["type"] == "text":
                    collected_text += chunk["content"]
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk['content']})}\n\n"

                elif chunk["type"] == "tool_calls":
                    tool_calls_list = chunk["tool_calls"]

                elif chunk["type"] == "done":
                    finish_reason = chunk["finish_reason"]

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
