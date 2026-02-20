"""Abstract LLM provider protocol."""

from collections.abc import Generator
from typing import Protocol

from app.services.tax.llm.types import StreamEvent


class LLMProvider(Protocol):
    def stream_chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> Generator[StreamEvent, None, None]: ...
