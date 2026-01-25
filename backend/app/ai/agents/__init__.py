"""Document verification agents module.

This module provides specialized AI agents for verifying different types
of documents. Each agent has domain-specific knowledge and validation rules.

Available Agents:
- InvoiceVerificationAgent: Sales/purchase invoices, credit notes
- BankStatementVerificationAgent: Bank statements
- ReceiptVerificationAgent: Receipts and expense documentation
- VATCertificateVerificationAgent: VAT registration certificates
- ContractVerificationAgent: Business contracts and agreements
- PayrollVerificationAgent: Payroll records and payslips

Usage:
    from app.ai.agents import AgentRegistry, verify_document

    # Using the registry
    registry = AgentRegistry(ai_provider)
    result = await registry.verify_document("INVOICE", extracted_data)

    # Or using the convenience function
    result = await verify_document(ai_provider, "INVOICE", extracted_data)
"""

from .base import (
    Anomaly,
    BaseDocumentAgent,
    Severity,
    VerificationResult,
)
from .bank_statement import BankStatementVerificationAgent
from .contract import ContractVerificationAgent
from .invoice import InvoiceVerificationAgent
from .payroll import PayrollVerificationAgent
from .receipt import ReceiptVerificationAgent
from .registry import AgentRegistry, verify_document
from .vat_certificate import VATCertificateVerificationAgent

__all__ = [
    # Base classes
    "BaseDocumentAgent",
    "VerificationResult",
    "Anomaly",
    "Severity",
    # Specialized agents
    "InvoiceVerificationAgent",
    "BankStatementVerificationAgent",
    "ReceiptVerificationAgent",
    "VATCertificateVerificationAgent",
    "ContractVerificationAgent",
    "PayrollVerificationAgent",
    # Registry
    "AgentRegistry",
    "verify_document",
]
