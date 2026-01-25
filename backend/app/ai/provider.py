"""Abstract AI provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def extract_document_data(
        self, document_content: bytes, content_type: str, filename: str
    ) -> dict[str, Any]:
        """Extract structured data from a document.

        Args:
            document_content: Raw document content (PDF, image, etc.)
            content_type: MIME type of the document
            filename: Original filename

        Returns:
            Dictionary containing extracted fields
        """
        pass

    @abstractmethod
    async def validate_document(
        self, extracted_data: dict[str, Any], document_type: str
    ) -> dict[str, Any]:
        """Validate extracted document data for anomalies.

        Args:
            extracted_data: Previously extracted data
            document_type: Type of document (invoice, credit_note, etc.)

        Returns:
            Dictionary containing validation results and anomalies
        """
        pass

    @abstractmethod
    async def generate_chaser_message(
        self, missing_items: list[str], recipient_name: str, due_date: str
    ) -> str:
        """Generate a professional chaser email message.

        Args:
            missing_items: List of missing evidence items
            recipient_name: Name of the recipient
            due_date: Due date for the evidence

        Returns:
            Generated email message body
        """
        pass

    @abstractmethod
    async def analyze_text(self, text: str, prompt: str) -> str:
        """General text analysis with custom prompt.

        Args:
            text: Text to analyze
            prompt: Custom prompt for analysis

        Returns:
            Analysis result
        """
        pass

    async def generate_text(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Generate text based on system and user prompts.

        Args:
            system_prompt: System-level instructions
            user_prompt: User prompt/request

        Returns:
            Generated text
        """
        # Default implementation combines prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        return await self.analyze_text("", full_prompt)

    async def close(self) -> None:
        """Optional cleanup hook for providers with async clients."""
        return None
