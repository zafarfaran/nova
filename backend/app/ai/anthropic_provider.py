"""Anthropic Claude AI provider implementation."""

import base64
import json
import logging
from typing import Any

import anthropic

from app.ai.prompts.extraction import (
    DOCUMENT_TYPE_DETECTION_PROMPT,
    get_extraction_prompt,
)
from app.ai.prompts.validation import ANOMALY_DETECTION_PROMPT, CHASER_EMAIL_PROMPT
from app.ai.provider import AIProvider
from app.config import get_settings


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider for document processing."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
        self.logger = logging.getLogger(__name__)

    def _get_media_type(self, content_type: str) -> str:
        """Map content type to Anthropic's supported media types."""
        media_type_map = {
            "image/jpeg": "image/jpeg",
            "image/png": "image/png",
            "image/gif": "image/gif",
            "image/webp": "image/webp",
            "application/pdf": "application/pdf",
        }
        return media_type_map.get(content_type, "image/jpeg")

    async def _analyze_image(
        self, content: bytes, content_type: str, prompt: str
    ) -> str:
        """Analyze an image using Claude Vision."""
        base64_data = base64.b64encode(content).decode("utf-8")
        media_type = self._get_media_type(content_type)

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return message.content[0].text if message.content else ""

    async def _analyze_text(self, prompt: str) -> str:
        """Analyze text using Claude."""
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text if message.content else ""

    async def extract_document_data(
        self, document_content: bytes, content_type: str, filename: str
    ) -> dict[str, Any]:
        """Extract structured data from a document."""
        self.logger.info(
            "Anthropic extraction start (filename=%s, content_type=%s, size=%s bytes)",
            filename,
            content_type,
            len(document_content),
        )
        # First detect document type
        type_response = await self._analyze_image(
            document_content, content_type, DOCUMENT_TYPE_DETECTION_PROMPT
        )

        try:
            # Try to extract JSON from the response
            type_data = self._extract_json(type_response)
            doc_type = type_data.get("document_type", "invoice")
        except (json.JSONDecodeError, ValueError):
            doc_type = "invoice"
        self.logger.info("Anthropic detected document type: %s", doc_type)

        # Get appropriate extraction prompt
        extraction_prompt = get_extraction_prompt(doc_type)

        # Extract data
        self.logger.info("Anthropic extraction prompt prepared for type=%s", doc_type)
        extraction_response = await self._analyze_image(
            document_content, content_type, extraction_prompt
        )

        try:
            extracted_data = self._extract_json(extraction_response)
            extracted_data["detected_document_type"] = doc_type
            self.logger.info(
                "Anthropic extraction complete (fields=%s)",
                len(extracted_data),
            )
            return extracted_data
        except (json.JSONDecodeError, ValueError):
            self.logger.warning("Anthropic extraction response JSON parse failed")
            return {
                "error": "Failed to parse extraction response",
                "raw_response": extraction_response,
                "detected_document_type": doc_type,
            }

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from text that might contain markdown code blocks."""
        # Try direct parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return json.loads(text[start:end].strip())

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return json.loads(text[start:end].strip())

        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])

        raise ValueError("No JSON found in response")

    async def validate_document(
        self, extracted_data: dict[str, Any], document_type: str
    ) -> dict[str, Any]:
        """Validate extracted document data for anomalies."""
        prompt = ANOMALY_DETECTION_PROMPT.format(
            extracted_data=json.dumps(extracted_data, indent=2, default=str)
        )

        response = await self._analyze_text(prompt)

        try:
            return self._extract_json(response)
        except (json.JSONDecodeError, ValueError):
            return {
                "is_valid": False,
                "anomalies": [
                    {
                        "field": "parsing",
                        "issue": "Failed to parse validation response",
                        "severity": "medium",
                        "suggestion": "Manual review required",
                    }
                ],
                "confidence_score": 0.0,
                "summary": "Validation parsing failed",
                "raw_response": response,
            }

    async def generate_chaser_message(
        self, missing_items: list[str], recipient_name: str, due_date: str
    ) -> str:
        """Generate a professional chaser email message."""
        prompt = CHASER_EMAIL_PROMPT.format(
            recipient_name=recipient_name,
            missing_items=", ".join(missing_items),
            due_date=due_date,
        )

        return await self._analyze_text(prompt)

    async def analyze_text(self, text: str, prompt: str) -> str:
        """General text analysis with custom prompt."""
        full_prompt = f"{prompt}\n\nText to analyze:\n{text}"
        return await self._analyze_text(full_prompt)

    async def close(self) -> None:
        """Close underlying async client."""
        try:
            await self.client.close()
        except Exception:
            self.logger.warning("Failed to close Anthropic client cleanly", exc_info=True)
