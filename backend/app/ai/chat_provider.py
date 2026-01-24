"""Abstract chat provider interface for AI assistants."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


class ChatProvider(ABC):
    """Abstract base class for chat AI providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send a chat message and get a response.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions
            tool_choice: How to handle tool selection ("auto", "none", etc.)

        Returns:
            Response dict with content, tool_calls, and finish_reason
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Send a chat message and stream the response.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions
            tool_choice: How to handle tool selection

        Yields:
            Dicts with type (text/tool_use/done) and relevant data
        """
        pass
