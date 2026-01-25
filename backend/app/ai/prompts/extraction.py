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

PAYROLL_EXTRACTION_PROMPT = """Analyze this payroll/payslip document and extract the following information in JSON format:

Required fields:
- employee_name: Full name of the employee
- employee_id: Employee number or ID if shown
- ni_number: National Insurance number (format: AB123456C)
- tax_code: Current tax code (e.g., 1257L, BR, etc.)
- pay_period: Pay period description (e.g., "Month 9 2024", "Week 34")
- pay_date: Payment date (format: YYYY-MM-DD)

Earnings:
- basic_pay: Basic salary amount (numeric)
- overtime: Overtime pay if applicable (numeric)
- bonus: Bonus amount if applicable (numeric)
- gross_pay: Total gross pay (numeric)

Deductions:
- paye_tax: Income tax / PAYE deduction (numeric)
- national_insurance: Employee NI contribution (numeric)
- pension_employee: Employee pension contribution (numeric)
- student_loan: Student loan deduction if applicable (numeric)
- total_deductions: Total deductions (numeric)

Net Pay:
- net_pay: Take-home pay (numeric)

Year to Date (if shown):
- ytd_gross: Year-to-date gross pay
- ytd_tax: Year-to-date tax paid
- ytd_ni: Year-to-date NI paid

Employer Contributions (if shown):
- employer_ni: Employer NI contribution
- employer_pension: Employer pension contribution

If a field cannot be found, set it to null.
Return only valid JSON, no additional text.

Example response:
{
    "employee_name": "John Smith",
    "employee_id": "EMP001",
    "ni_number": "AB123456C",
    "tax_code": "1257L",
    "pay_period": "Month 9 2024",
    "pay_date": "2024-09-25",
    "basic_pay": 3000.00,
    "overtime": 150.00,
    "bonus": null,
    "gross_pay": 3150.00,
    "paye_tax": 420.00,
    "national_insurance": 252.00,
    "pension_employee": 157.50,
    "student_loan": null,
    "total_deductions": 829.50,
    "net_pay": 2320.50,
    "ytd_gross": 28350.00,
    "ytd_tax": 3780.00,
    "ytd_ni": 2268.00,
    "employer_ni": 378.00,
    "employer_pension": 94.50
}"""

VAT_CERTIFICATE_EXTRACTION_PROMPT = """Analyze this VAT registration certificate and extract the following information in JSON format:

Required fields:
- vat_number: VAT registration number
- effective_date: Date VAT registration became effective (format: YYYY-MM-DD)
- business_name: Registered business name
- trading_name: Trading name if different from business name
- business_address: Full registered address
- business_type: Type of entity (Limited Company, Sole Trader, Partnership, etc.)

VAT Scheme details:
- vat_scheme: Type of VAT scheme (Standard, Flat Rate, Cash Accounting, etc.)
- accounting_period: VAT return period (Monthly, Quarterly, Annual)

If a field cannot be found, set it to null.
Return only valid JSON, no additional text."""

CONTRACT_EXTRACTION_PROMPT = """Analyze this contract/agreement document and extract the following information in JSON format:

Required fields:
- contract_type: Type of contract (Service Agreement, Employment, Supply, etc.)
- contract_date: Date of the contract (format: YYYY-MM-DD)
- effective_date: When contract takes effect (format: YYYY-MM-DD)

Parties:
- parties: Array of parties with:
    - name: Party name
    - role: Role in contract (Client, Provider, Employer, Employee, etc.)
    - address: Address if shown
    - company_number: Company registration number if shown

Terms:
- start_date: Contract start date
- end_date: Contract end date (or "ongoing" if no end date)
- term_length: Duration of contract
- notice_period: Notice period for termination
- renewal_terms: Auto-renewal terms if specified

Financial:
- total_value: Total contract value if specified (numeric)
- payment_amount: Regular payment amount (numeric)
- payment_frequency: Payment frequency (weekly, monthly, annually)
- currency: Currency code

VAT:
- vat_applicable: Whether VAT applies (true/false)
- vat_rate: VAT rate if applicable

If a field cannot be found, set it to null.
Return only valid JSON, no additional text."""

DOCUMENT_TYPE_DETECTION_PROMPT = """Analyze this document and determine its type. Return one of the following types in JSON format:

Types:
- invoice: A sales or purchase invoice
- credit_note: A credit note or credit memo
- debit_note: A debit note
- receipt: A purchase receipt
- bank_statement: A bank statement
- payroll: A payslip or payroll document
- contract: A contract or agreement
- vat_certificate: VAT registration certificate
- import_declaration: Import customs declaration
- export_declaration: Export customs declaration
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
        "payroll": PAYROLL_EXTRACTION_PROMPT,
        "vat_certificate": VAT_CERTIFICATE_EXTRACTION_PROMPT,
        "contract": CONTRACT_EXTRACTION_PROMPT,
    }
    return prompts.get(document_type, INVOICE_EXTRACTION_PROMPT)
