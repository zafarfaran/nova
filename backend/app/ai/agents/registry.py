"""Agent registry for document verification agents.

This module provides a factory/registry pattern for managing specialized
document verification agents. It allows easy lookup of the appropriate
agent based on document type.
"""

from typing import Any, Type

from .base import BaseDocumentAgent, VerificationResult
from .bank_statement import BankStatementVerificationAgent
from .contract import ContractVerificationAgent
from .invoice import InvoiceVerificationAgent
from .payroll import PayrollVerificationAgent
from .receipt import ReceiptVerificationAgent
from .vat_certificate import VATCertificateVerificationAgent


class AgentRegistry:
    """Registry for document verification agents.

    Provides centralized management and lookup of specialized agents
    based on document type.
    """

    # Map document types to their specialized agents
    _agents: dict[str, Type[BaseDocumentAgent]] = {
        # Invoice types
        "INVOICE": InvoiceVerificationAgent,
        "SALES_INVOICE": InvoiceVerificationAgent,
        "PURCHASE_INVOICE": InvoiceVerificationAgent,
        "CREDIT_NOTE": InvoiceVerificationAgent,

        # Bank statements
        "BANK_STATEMENT": BankStatementVerificationAgent,

        # Receipts
        "RECEIPT": ReceiptVerificationAgent,
        "EXPENSE_RECEIPT": ReceiptVerificationAgent,

        # Payroll
        "PAYROLL": PayrollVerificationAgent,
        "PAYSLIP": PayrollVerificationAgent,
        "PAYROLL_RECORD": PayrollVerificationAgent,

        # VAT certificates
        "VAT_CERTIFICATE": VATCertificateVerificationAgent,
        "VAT_REGISTRATION": VATCertificateVerificationAgent,

        # Contracts
        "CONTRACT": ContractVerificationAgent,
        "AGREEMENT": ContractVerificationAgent,
        "SERVICE_AGREEMENT": ContractVerificationAgent,
    }

    # Default agent for unknown document types
    _default_agent: Type[BaseDocumentAgent] = InvoiceVerificationAgent

    def __init__(self, ai_provider: Any):
        """Initialize the registry with an AI provider.

        Args:
            ai_provider: The AI provider to use for all agents
        """
        self.ai_provider = ai_provider
        self._instances: dict[str, BaseDocumentAgent] = {}

    def get_agent(self, document_type: str) -> BaseDocumentAgent:
        """Get the appropriate agent for a document type.

        Args:
            document_type: The type of document (e.g., "INVOICE", "BANK_STATEMENT")

        Returns:
            The specialized agent for the document type
        """
        # Normalize document type
        doc_type = document_type.upper().strip() if document_type else "UNKNOWN"

        # Check if we already have an instance
        if doc_type in self._instances:
            return self._instances[doc_type]

        # Get the agent class
        agent_class = self._agents.get(doc_type, self._default_agent)

        # Create and cache the instance
        agent = agent_class(self.ai_provider)
        self._instances[doc_type] = agent

        return agent

    async def verify_document(
        self, document_type: str, extracted_data: dict[str, Any]
    ) -> VerificationResult:
        """Verify a document using the appropriate specialized agent.

        This is the main entry point for document verification. It automatically
        selects the right agent based on document type and runs verification.

        Args:
            document_type: The type of document
            extracted_data: Dictionary of extracted document data

        Returns:
            VerificationResult with detailed findings
        """
        agent = self.get_agent(document_type)
        return await agent.verify(extracted_data)

    @classmethod
    def register_agent(cls, document_type: str, agent_class: Type[BaseDocumentAgent]) -> None:
        """Register a new agent type.

        Allows extending the registry with custom agents.

        Args:
            document_type: The document type this agent handles
            agent_class: The agent class to register
        """
        cls._agents[document_type.upper()] = agent_class

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of supported document types.

        Returns:
            List of document type strings
        """
        return list(cls._agents.keys())

    @classmethod
    def is_supported(cls, document_type: str) -> bool:
        """Check if a document type is supported.

        Args:
            document_type: The document type to check

        Returns:
            True if the document type has a specialized agent
        """
        return document_type.upper() in cls._agents


# Convenience function for quick verification
async def verify_document(
    ai_provider: Any, document_type: str, extracted_data: dict[str, Any]
) -> VerificationResult:
    """Verify a document using the appropriate specialized agent.

    This is a convenience function that creates a registry and verifies
    a document in one call.

    Args:
        ai_provider: The AI provider to use
        document_type: The type of document
        extracted_data: Dictionary of extracted document data

    Returns:
        VerificationResult with detailed findings
    """
    registry = AgentRegistry(ai_provider)
    return await registry.verify_document(document_type, extracted_data)
