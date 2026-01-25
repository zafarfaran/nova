"""Base document verification agent interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity levels for anomalies."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Anomaly:
    """Represents a detected anomaly in a document."""
    field: str
    issue: str
    severity: Severity
    suggestion: str
    expected_value: str | None = None
    actual_value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "issue": self.issue,
            "severity": self.severity.value,
            "suggestion": self.suggestion,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
        }


@dataclass
class VerificationResult:
    """Result of document verification by an agent."""
    is_valid: bool
    confidence_score: float  # 0.0 to 1.0
    anomalies: list[Anomaly] = field(default_factory=list)
    summary: str = ""
    document_type: str = ""
    extracted_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "confidence_score": self.confidence_score,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "summary": self.summary,
            "document_type": self.document_type,
            "extracted_fields": self.extracted_fields,
        }


class BaseDocumentAgent(ABC):
    """Abstract base class for document verification agents.

    Each specialized agent should implement:
    - get_document_type(): Returns the document type this agent handles
    - get_required_fields(): Returns list of required fields for this document type
    - get_validation_rules(): Returns specific validation rules
    - get_system_prompt(): Returns the AI system prompt for this document type
    - verify(): Main verification method
    """

    def __init__(self, ai_provider: Any):
        """Initialize the agent with an AI provider.

        Args:
            ai_provider: The AI provider (Anthropic/OpenAI) to use for analysis
        """
        self.ai_provider = ai_provider

    @property
    @abstractmethod
    def document_type(self) -> str:
        """Return the document type this agent handles."""
        pass

    @property
    @abstractmethod
    def required_fields(self) -> list[str]:
        """Return list of required fields for this document type."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the specialized system prompt for this agent."""
        pass

    @abstractmethod
    def get_validation_prompt(self, extracted_data: dict[str, Any]) -> str:
        """Return the validation prompt with the extracted data."""
        pass

    @abstractmethod
    async def verify(self, extracted_data: dict[str, Any]) -> VerificationResult:
        """Verify the document and return results.

        Args:
            extracted_data: Dictionary of extracted document data

        Returns:
            VerificationResult with validation findings
        """
        pass

    def check_required_fields(self, extracted_data: dict[str, Any]) -> list[Anomaly]:
        """Check if all required fields are present.

        Args:
            extracted_data: Dictionary of extracted document data

        Returns:
            List of anomalies for missing required fields
        """
        anomalies = []
        for field in self.required_fields:
            value = extracted_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                anomalies.append(Anomaly(
                    field=field,
                    issue=f"Required field '{field}' is missing or empty",
                    severity=Severity.HIGH,
                    suggestion=f"Ensure the document contains a valid {field.replace('_', ' ')}",
                ))
        return anomalies

    def _parse_ai_response(self, response: str) -> dict[str, Any]:
        """Parse the AI response into structured data.

        Args:
            response: Raw AI response text

        Returns:
            Parsed dictionary with validation results
        """
        import json
        import re

        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: return basic structure
        return {
            "is_valid": True,
            "anomalies": [],
            "confidence_score": 0.5,
            "summary": response[:500] if response else "Unable to parse response",
        }
