"""OpenAI chat provider implementation."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI, OpenAI

from app.ai.chat_provider import ChatProvider
from app.config import get_settings


class OpenAIChatProvider(ChatProvider):
    """OpenAI GPT chat provider with function calling support."""

    def __init__(self):
        settings = get_settings()
        self.sync_client = OpenAI(api_key=settings.openai_api_key)
        self.async_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o"

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send a chat message and get a response."""
        kwargs = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = await self.async_client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        result = {
            "content": choice.message.content or "",
            "finish_reason": choice.finish_reason,
            "tool_calls": [],
        }

        if choice.message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": json.loads(tc.function.arguments) if tc.function.arguments.strip() else {},
                }
                for tc in choice.message.tool_calls
            ]

        return result

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Send a chat message and stream the response."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = self.sync_client.chat.completions.create(**kwargs)

        tool_calls_data: dict[int, dict] = {}
        finish_reason = None

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            finish_reason = chunk.choices[0].finish_reason if chunk.choices else None

            if delta:
                # Stream text content
                if delta.content:
                    yield {"type": "text", "content": delta.content}

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

        # Yield complete tool calls and finish reason
        if tool_calls_data:
            tool_calls = [
                {
                    "id": tool_calls_data[idx]["id"],
                    "name": tool_calls_data[idx]["name"],
                    "arguments": tool_calls_data[idx]["arguments"],
                }
                for idx in sorted(tool_calls_data.keys())
            ]
            yield {"type": "tool_calls", "tool_calls": tool_calls}

        yield {"type": "done", "finish_reason": finish_reason}
