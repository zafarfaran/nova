"""OpenAI AI provider implementation."""

import base64
import json
from typing import Any

from openai import AsyncOpenAI

from app.ai.prompts.extraction import (
    DOCUMENT_TYPE_DETECTION_PROMPT,
    get_extraction_prompt,
)
from app.ai.prompts.validation import ANOMALY_DETECTION_PROMPT, CHASER_EMAIL_PROMPT
from app.ai.provider import AIProvider
from app.config import get_settings


class OpenAIProvider(AIProvider):
    """OpenAI GPT-4 Vision provider for document processing."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o"  # Vision-capable model

    async def _analyze_image(self, content: bytes, content_type: str, prompt: str) -> str:
        """Analyze an image using GPT-4 Vision."""
        base64_image = base64.b64encode(content).decode("utf-8")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
        )

        return response.choices[0].message.content or ""

    async def _analyze_text(self, prompt: str) -> str:
        """Analyze text using GPT-4."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )

        return response.choices[0].message.content or ""

    async def extract_document_data(
        self, document_content: bytes, content_type: str, filename: str
    ) -> dict[str, Any]:
        """Extract structured data from a document."""
        # First detect document type
        type_response = await self._analyze_image(
            document_content, content_type, DOCUMENT_TYPE_DETECTION_PROMPT
        )

        try:
            type_data = json.loads(type_response)
            doc_type = type_data.get("document_type", "invoice")
        except json.JSONDecodeError:
            doc_type = "invoice"

        # Get appropriate extraction prompt
        extraction_prompt = get_extraction_prompt(doc_type)

        # Extract data
        extraction_response = await self._analyze_image(
            document_content, content_type, extraction_prompt
        )

        try:
            extracted_data = json.loads(extraction_response)
            extracted_data["detected_document_type"] = doc_type
            return extracted_data
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse extraction response",
                "raw_response": extraction_response,
                "detected_document_type": doc_type,
            }

    async def validate_document(
        self, extracted_data: dict[str, Any], document_type: str
    ) -> dict[str, Any]:
        """Validate extracted document data for anomalies."""
        prompt = ANOMALY_DETECTION_PROMPT.format(
            extracted_data=json.dumps(extracted_data, indent=2, default=str)
        )

        response = await self._analyze_text(prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
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
