"""Prompts for document data extraction."""

INVOICE_EXTRACTION_PROMPT = """Analyze this invoice document and extract the following information in JSON format:

Required fields:
- invoice_number: The invoice number/reference
- invoice_date: Date of the invoice (format: YYYY-MM-DD)
- supplier_name: Name of the supplier/vendor
- supplier_vat_number: VAT registration number of the supplier (UK format: GB followed by 9 or 12 digits)
- customer_name: Name of the customer
- customer_vat_number: VAT registration number of the customer if present
- net_amount: Net amount before VAT (numeric, no currency symbols)
- vat_amount: VAT amount (numeric, no currency symbols)
- gross_amount: Total amount including VAT (numeric, no currency symbols)
- vat_rate: VAT rate applied (as percentage, e.g., 20 for 20%)
- currency: Currency code (e.g., GBP, EUR, USD)
- description: Brief description of goods/services

Additional fields if available:
- payment_terms: Payment terms mentioned
- due_date: Payment due date
- po_number: Purchase order number
- line_items: Array of line items with description, quantity, unit_price, vat_rate, total

If a field cannot be found, set it to null.
Return only valid JSON, no additional text.

Example response:
{
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15",
    "supplier_name": "Acme Ltd",
    "supplier_vat_number": "GB123456789",
    "customer_name": "Test Company",
    "customer_vat_number": "GB987654321",
    "net_amount": 1000.00,
    "vat_amount": 200.00,
    "gross_amount": 1200.00,
    "vat_rate": 20,
    "currency": "GBP",
    "description": "Consulting services",
    "payment_terms": "Net 30",
    "due_date": "2024-02-15",
    "po_number": "PO-123",
    "line_items": [
        {
            "description": "Consulting services",
            "quantity": 10,
            "unit_price": 100.00,
            "vat_rate": 20,
            "total": 1000.00
        }
    ]
}"""

CREDIT_NOTE_EXTRACTION_PROMPT = """Analyze this credit note document and extract the following information in JSON format:

Required fields:
- credit_note_number: The credit note number/reference
- credit_note_date: Date of the credit note (format: YYYY-MM-DD)
- original_invoice_number: Reference to the original invoice if mentioned
- supplier_name: Name of the supplier/vendor issuing the credit
- supplier_vat_number: VAT registration number of the supplier
- customer_name: Name of the customer
- customer_vat_number: VAT registration number of the customer if present
- net_amount: Net amount before VAT (numeric, positive value)
- vat_amount: VAT amount (numeric, positive value)
- gross_amount: Total amount including VAT (numeric, positive value)
- vat_rate: VAT rate applied
- currency: Currency code
- reason: Reason for the credit note

If a field cannot be found, set it to null.
Return only valid JSON, no additional text."""

BANK_STATEMENT_EXTRACTION_PROMPT = """Analyze this bank statement and extract the following information in JSON format:

Required fields:
- account_name: Name on the account
- account_number: Bank account number (last 4 digits only for security)
- sort_code: Bank sort code
- statement_period_start: Start date of the statement period (format: YYYY-MM-DD)
- statement_period_end: End date of the statement period (format: YYYY-MM-DD)
- opening_balance: Opening balance
- closing_balance: Closing balance
- currency: Currency code
- transactions: Array of transactions with:
    - date: Transaction date
    - description: Transaction description
    - amount: Transaction amount (positive for credits, negative for debits)
    - balance: Running balance after transaction
    - type: "credit" or "debit"

If a field cannot be found, set it to null.
Return only valid JSON, no additional text."""

RECEIPT_EXTRACTION_PROMPT = """Analyze this receipt and extract the following information in JSON format:

Required fields:
- receipt_date: Date of the receipt (format: YYYY-MM-DD)
- vendor_name: Name of the vendor/shop
- vendor_vat_number: VAT registration number if present
- net_amount: Net amount before VAT
- vat_amount: VAT amount
- gross_amount: Total amount
- vat_rate: VAT rate applied
- payment_method: Payment method (cash, card, etc.)
- items: Array of purchased items with description and price

If a field cannot be found, set it to null.
Return only valid JSON, no additional text."""

DOCUMENT_TYPE_DETECTION_PROMPT = """Analyze this document and determine its type. Return one of the following types in JSON format:

Types:
- invoice: A sales or purchase invoice
- credit_note: A credit note or credit memo
- debit_note: A debit note
- receipt: A purchase receipt
- bank_statement: A bank statement
- contract: A contract or agreement
- import_declaration: Import customs declaration
- export_declaration: Export customs declaration
- vat_certificate: VAT registration certificate
- other: Any other document type

Return JSON format:
{
    "document_type": "invoice",
    "confidence": 0.95,
    "reasoning": "Document contains invoice number, supplier details, and VAT breakdown typical of a UK invoice"
}"""


def get_extraction_prompt(document_type: str) -> str:
    """Get the appropriate extraction prompt for a document type."""
    prompts = {
        "invoice": INVOICE_EXTRACTION_PROMPT,
        "credit_note": CREDIT_NOTE_EXTRACTION_PROMPT,
        "bank_statement": BANK_STATEMENT_EXTRACTION_PROMPT,
        "receipt": RECEIPT_EXTRACTION_PROMPT,
    }
    return prompts.get(document_type, INVOICE_EXTRACTION_PROMPT)
