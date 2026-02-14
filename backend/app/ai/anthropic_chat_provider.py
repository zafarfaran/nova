"""Anthropic Claude chat provider implementation."""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import anthropic

from app.ai.chat_provider import ChatProvider
from app.config import get_settings
from app.core.llm_instrumentation import LLMInstrumentation


class AnthropicChatProvider(ChatProvider):
    """Anthropic Claude chat provider with tool use support."""

    def __init__(self):
        settings = get_settings()
        self.sync_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
        self.logger = logging.getLogger(__name__)
        self.instrumentation = LLMInstrumentation("anthropic", self.model)

    def _convert_tools_to_anthropic(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-style tools to Anthropic format."""
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"],
                })
        return anthropic_tools

    def _extract_system_message(self, messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        """Extract system message and convert tool messages to Anthropic format."""
        system_content = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            elif msg["role"] == "tool":
                # Convert OpenAI-style tool message to Anthropic format
                user_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg["tool_call_id"],
                            "content": msg["content"],
                        }
                    ],
                })
            elif msg["role"] == "assistant" and msg.get("tool_calls"):
                # Convert OpenAI-style tool calls to Anthropic format
                content_blocks = []
                if msg.get("content"):
                    content_blocks.append({"type": "text", "text": msg["content"]})

                for tc in msg["tool_calls"]:
                    # Safely parse tool arguments
                    args = tc["function"]["arguments"]
                    if isinstance(args, str):
                        tool_input = json.loads(args) if args.strip() else {}
                    else:
                        tool_input = args if args else {}

                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": tool_input,
                    })

                user_messages.append({
                    "role": "assistant",
                    "content": content_blocks,
                })
            else:
                user_messages.append(msg)

        return system_content, user_messages

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send a chat message and get a response."""
        async with self.instrumentation.track_call(
            "chat",
            request_data={
                "messages_count": len(messages),
                "has_tools": tools is not None and len(tools) > 0,
                "tool_choice": tool_choice,
            },
            log_response=True,
        ):
            system_content, user_messages = self._extract_system_message(messages)

            kwargs = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": user_messages,
            }

            if system_content:
                kwargs["system"] = system_content

            if tools:
                kwargs["tools"] = self._convert_tools_to_anthropic(tools)

            response = await self.async_client.messages.create(**kwargs)
            
            self.instrumentation.record_response(response)

            result = {
                "content": "",
                "finish_reason": response.stop_reason,
                "tool_calls": [],
            }

            # Extract text content and tool uses
            for block in response.content:
                if block.type == "text":
                    result["content"] += block.text
                elif block.type == "tool_use":
                    result["tool_calls"].append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            return result

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Send a chat message and stream the response."""
        async with self.instrumentation.track_call(
            "chat_stream",
            request_data={
                "messages_count": len(messages),
                "has_tools": tools is not None and len(tools) > 0,
                "tool_choice": tool_choice,
            },
            log_response=False,  # Don't log full streamed responses
        ):
            system_content, user_messages = self._extract_system_message(messages)

            kwargs = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": user_messages,
            }

            if system_content:
                kwargs["system"] = system_content

            if tools:
                kwargs["tools"] = self._convert_tools_to_anthropic(tools)

            # Track tool calls being built
            current_tool_calls: dict[str, dict] = {}
            finish_reason = None
            full_content = ""

            async with self.async_client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    # Handle different event types
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_calls[event.content_block.id] = {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": "",
                            }

                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            # Text delta
                            full_content += event.delta.text
                            yield {"type": "text", "content": event.delta.text}
                        elif hasattr(event.delta, "partial_json"):
                            # Tool input delta
                            if event.index < len(current_tool_calls):
                                tool_id = list(current_tool_calls.keys())[event.index]
                                current_tool_calls[tool_id]["input"] += event.delta.partial_json

                    elif event.type == "message_stop":
                        finish_reason = stream.current_message_snapshot.stop_reason
                        # Try to get usage from snapshot
                        if hasattr(stream, "current_message_snapshot") and hasattr(stream.current_message_snapshot, "usage"):
                            self.instrumentation.record_response(stream.current_message_snapshot)
                        else:
                            # Approximate for streaming
                            class MockResponse:
                                def __init__(self, content_length):
                                    self.content_length = content_length
                            self.instrumentation.record_response(MockResponse(len(full_content)))

            # Yield complete tool calls if any
            if current_tool_calls:
                tool_calls = []
                for tool_data in current_tool_calls.values():
                    try:
                        tool_calls.append({
                            "id": tool_data["id"],
                            "name": tool_data["name"],
                            "arguments": tool_data["input"],
                        })
                    except json.JSONDecodeError:
                        # If JSON is malformed, pass as string
                        tool_calls.append({
                            "id": tool_data["id"],
                            "name": tool_data["name"],
                            "arguments": tool_data["input"],
                        })
                yield {"type": "tool_calls", "tool_calls": tool_calls}

            yield {"type": "done", "finish_reason": finish_reason}
