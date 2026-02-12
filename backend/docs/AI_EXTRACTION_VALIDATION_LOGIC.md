# AI Extraction, Normalization, and Validation Logic

## Overview

This document explains the complete AI pipeline for processing financial documents (invoices, bank statements, receipts, payroll, etc.) in the Nova accounting system. The system uses a **hybrid approach** combining traditional PDF parsing with LLM-based extraction and validation.

---

## Architecture Overview

```
PDF/Image Upload
    ↓
[1] Structure Extraction (pdfplumber)
    ↓
[2] Document Type Detection
    ↓
[3] Key-Value Pair Extraction (Regex + Pattern Matching)
    ↓
[4] AI-Powered Extraction (OpenAI GPT-4o / Anthropic Claude)
    ↓
[5] Data Merging & Normalization
    ↓
[6] Rule-Based Validation
    ↓
[7] AI Anomaly Detection (Specialized Agents)
    ↓
Validated Document
```

---

## Phase 1: PDF Structure Extraction

**Location:** `backend/app/services/documents/extraction.py` → `PDFExtractionService._extract_structure()`

### Process

1. **Text Extraction with Layout Preservation**
   - Uses `pdfplumber` to extract text while preserving spatial relationships
   - Groups words into lines based on vertical position (`y_tolerance=5px`)
   - Maintains font information (size, name, bold) for semantic understanding

2. **Document Region Classification**
   - **Header**: Top 15% of page
   - **Footer**: Bottom 10% of page
   - **Sidebar**: Left/right 15% margins
   - **Body**: Main content area
   - **Table**: Detected table structures

3. **Table Detection**
   - Uses `pdfplumber.find_tables()` with line-based detection
   - Extracts headers and rows with bounding box coordinates
   - Confidence scoring based on header presence

4. **Text Block Extraction**
   - Each block contains:
     - Text content
     - Position (x0, y0, x1, y1)
     - Font metadata
     - Region classification

### Output: `DocumentStructure`
```python
{
    "text_blocks": [TextBlock(...)],
    "tables": [ExtractedTable(...)],
    "key_value_pairs": [KeyValuePair(...)],
    "full_text": "Complete document text...",
    "page_count": 3,
    "metadata": {...}
}
```

---

## Phase 2: Document Type Detection

**Location:** `PDFExtractionService._detect_document_type()`

### Strategy: Keyword Scoring

1. **Keyword Matching**
   - Each document type has a list of known field keywords
   - Example for invoices: `["invoice number", "invoice date", "supplier", "vat", "total"]`
   - Scores each document type based on keyword frequency

2. **Indicator-Based Fallback**
   - If scoring is inconclusive, checks for specific indicators:
     - `"invoice"` or `"inv no"` → invoice
     - `"statement"` + `"bank"` → bank_statement
     - `"receipt"` → receipt
     - `"payslip"` or `"payroll"` → payroll

3. **Default**
   - Falls back to `"other"` if no match found

### Why This Matters
- Document type determines which extraction prompt to use
- Affects validation rules applied later
- Enables type-specific normalization

---

## Phase 3: Key-Value Pair Extraction

**Location:** `PDFExtractionService._extract_key_values()`

### Pattern-Based Extraction

1. **Regex Patterns**
   ```python
   # Pattern: "Key: Value"
   r"([A-Za-z][A-Za-z\s]+?)[\s]*[:]\s*([^\n]+)"
   
   # Pattern: Known field labels
   r"(Invoice\s*(?:No|Number|#)|Date|Total|VAT|Tax|Amount)[\s:]*([^\n]+)"
   ```

2. **Text Block Analysis**
   - Scans text blocks for colon-separated pairs
   - Filters by relevance to document type
   - Assigns confidence scores (0.7-0.9)

3. **Known Fields Dictionary**
   - Each document type has a curated list of expected fields
   - Only extracts pairs matching known fields for that type
   - Reduces false positives

### Example Output
```python
[
    KeyValuePair(key="invoice_number", value="INV-2024-001", confidence=0.9),
    KeyValuePair(key="invoice_date", value="2024-01-15", confidence=0.9),
    KeyValuePair(key="total", value="£1,200.00", confidence=0.8)
]
```

---

## Phase 4: AI-Powered Extraction

**Location:** `PDFExtractionService._ai_extract()`

### LLM Integration

1. **Provider Selection**
   - **OpenAI GPT-4o**: Used for PDF text-based extraction
   - **Anthropic Claude**: Used for image-based extraction (if PDF extraction fails)
   - Both support structured JSON output

2. **Prompt Engineering**

   **Context Building:**
   ```python
   prompt = f"""
   {document_type_specific_prompt}
   
   === PRE-EXTRACTED CONTEXT ===
   Document has {page_count} page(s).
   Found {len(tables)} table(s).
   Pre-extracted key-value pairs:
     - invoice_number: INV-001
     - invoice_date: 2024-01-15
     ...
   
   === DOCUMENT TEXT ===
   {full_text[:15000]}  # Truncated to token limit
   """
   ```

   **Document-Type-Specific Prompts:**
   - Each document type has a tailored prompt with:
     - Required fields list
     - Field format specifications (e.g., dates as YYYY-MM-DD)
     - Example JSON structure
     - Special instructions (e.g., "Return ONLY valid JSON")

3. **LLM Call Configuration**
   ```python
   response = await ai_provider.client.chat.completions.create(
       model="gpt-4o",
       messages=[
           {
               "role": "system",
               "content": "You are a document data extraction specialist..."
           },
           {
               "role": "user",
               "content": full_prompt
           }
       ],
       max_tokens=4096,
       temperature=0.1  # Low temperature for consistency
   )
   ```

4. **JSON Parsing with Fallbacks**
   - First: Try parsing response as-is
   - Second: Extract JSON from markdown code blocks (```json ... ```)
   - Third: Find JSON object in text using regex
   - If all fail: Return empty dict (graceful degradation)

### Why AI Extraction?

- **Handles Complex Layouts**: AI understands context better than regex
- **Normalizes Variations**: "Invoice #", "Inv No", "Invoice Number" → `invoice_number`
- **Extracts Relationships**: Understands that "Net: £1000" + "VAT: £200" = "Total: £1200"
- **Table Understanding**: Can extract line items from complex table structures

---

## Phase 5: Data Merging & Normalization

**Location:** `backend/app/tasks/documents/document_tasks.py` → `_normalize_extracted_data()`

### Merging Strategy

1. **Priority Order**
   - **AI extraction** (highest priority) - usually most accurate
   - **Key-value pairs** (medium priority) - fills gaps
   - **Structure-based** (lowest priority) - fallback

2. **Normalization Rules**

   **Field Name Standardization:**
   ```python
   # Multiple variations → single field
   "supplier_name" ← ["supplier", "vendor", "seller", "from"]
   "customer_name" ← ["customer", "buyer", "bill_to", "client"]
   "gross_amount" ← ["gross_amount", "gross_total", "total"]
   ```

   **Nested Structure Flattening:**
   ```python
   # Input:
   {
       "supplier_details": {
           "name": "Acme Ltd",
           "vat_number": "GB123456789"
       }
   }
   
   # Output:
   {
       "supplier_name": "Acme Ltd",
       "supplier_vat_number": "GB123456789"
   }
   ```

3. **Document-Type-Specific Normalization**

   **Invoices:**
   - Extracts from `invoice_details`, `totals`, `amounts` nested objects
   - Maps `reference_number` → `invoice_number` if missing

   **Bank Statements:**
   - Flattens `account_details`, `statement_period`, `balances`, `summary`
   - Normalizes transaction arrays

   **Payroll:**
   - Extracts from `employee_details`, `pay_period`, `earnings`, `deductions`
   - Maps `take_home_pay` → `net_pay`

4. **Data Type Conversion**
   - **Dates**: Multiple format parsing (`%Y-%m-%d`, `%d/%m/%Y`, etc.)
   - **Amounts**: Removes currency symbols, commas → `Decimal`
   - **Arrays**: Ensures consistent structure for line items/transactions

### Output: Normalized Dictionary
```python
{
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15",
    "supplier_name": "Acme Ltd",
    "supplier_vat_number": "GB123456789",
    "net_amount": Decimal("1000.00"),
    "vat_amount": Decimal("200.00"),
    "gross_amount": Decimal("1200.00"),
    "currency": "GBP",
    "document_type": "invoice"
}
```

---

## Phase 6: Rule-Based Validation

**Location:** `backend/app/services/validation/service.py` → `ValidationService`

### Validation Architecture

1. **Document-Type Routing**
   ```python
   DOCUMENT_TYPE_VALIDATORS = {
       "invoice": "_validate_invoice",
       "bank_statement": "_validate_bank_statement",
       "receipt": "_validate_receipt",
       "payroll": "_validate_payroll",
       ...
   }
   ```

2. **Validation Rule Types**

   **Required Fields:**
   - Checks presence of critical fields
   - Example: Invoice must have `invoice_number`, `invoice_date`, `supplier_name`, `net_amount`, `vat_amount`, `gross_amount`

   **Calculation Verification:**
   ```python
   # Invoice: net + VAT = gross
   calculated_gross = net_amount + vat_amount
   difference = abs(calculated_gross - gross_amount)
   if difference > CALCULATION_TOLERANCE:  # £0.02
       → FAILED validation
   ```

   **Format Validation:**
   - VAT numbers: `GB` + 9 or 12 digits
   - NI numbers: `AB123456C` format
   - Tax codes: `1257L`, `BR`, `D0`, etc.
   - Bank account numbers: 8 digits
   - Sort codes: 6 digits

   **Business Logic:**
   - **Date in Period**: Invoice date must be within engagement period
   - **Duplicate Detection**: Check for existing invoices with same number
   - **VAT Rate**: Must be valid UK rate (0%, 5%, 20%)
   - **Receipt VAT Requirements**: Over £250 requires full VAT invoice details
   - **Payroll Calculations**: Gross - Deductions = Net (with tolerance)

3. **Validation Result Structure**
   ```python
   ValidationResult(
       document_id=123,
       rule_type=RuleType.TOTALS_MATCH,
       status=ValidationStatus.PASSED | FAILED | WARNING | SKIPPED,
       message="Invoice calculation verified",
       details="...",
       severity="high" | "medium" | "low",
       field_name="gross_amount",
       expected_value="1200.00",
       actual_value="1200.00",
       ai_reasoning={...}  # For AI-generated results
   )
   ```

### Example: Invoice Validation Flow

```python
def _validate_invoice(self, doc: Document) -> list[ValidationResult]:
    results = []
    
    # 1. Required fields
    results.append(self._validate_invoice_required_fields(doc))
    
    # 2. VAT number format
    results.append(self._validate_vat_number_format(doc))
    
    # 3. Date in period
    results.append(self._validate_date_in_period(doc))
    
    # 4. Totals match (net + VAT = gross)
    results.append(self._validate_invoice_totals(doc))
    
    # 5. VAT rate valid
    results.append(self._validate_vat_rate(doc))
    
    # 6. Duplicate detection
    results.append(self._validate_invoice_duplicate(doc))
    
    # 7. Currency validation
    results.append(self._validate_currency(doc))
    
    return results
```

---

## Phase 7: AI Anomaly Detection

**Location:** `ValidationService._validate_ai_anomaly()` → `AgentRegistry`

### Specialized Agent Architecture

1. **Agent Registry Pattern**
   ```python
   registry = AgentRegistry(ai_provider)
   agent = registry.get_agent(document_type)  # Returns specialized agent
   result = await agent.verify(extracted_data)
   ```

2. **Available Agents**

   **InvoiceVerificationAgent:**
   - Checks required fields
   - Verifies VAT calculations
   - Validates VAT rates
   - Checks date logic
   - AI-powered deep analysis

   **BankStatementVerificationAgent:**
   - Validates account details
   - Verifies balance reconciliation
   - Checks transaction consistency

   **ReceiptVerificationAgent:**
   - Validates VAT invoice requirements (over £250)
   - Checks date validity (4-year limit for VAT claims)
   - Verifies amount reasonableness

   **PayrollVerificationAgent:**
   - Validates NI number format
   - Checks tax code format
   - Verifies payroll calculations
   - Validates NI contribution thresholds

   **ContractVerificationAgent:**
   - Validates parties are distinct
   - Checks contract date logic
   - Verifies VAT treatment

   **VATCertificateVerificationAgent:**
   - Validates VAT number format
   - Checks effective date (not in future, not before 1973)

3. **Agent Verification Flow**

   **Step 1: Rule-Based Checks**
   ```python
   anomalies = []
   anomalies.extend(self.check_required_fields(extracted_data))
   anomalies.extend(self._verify_vat_calculation(extracted_data))
   anomalies.extend(self._verify_vat_rate(extracted_data))
   ```

   **Step 2: AI-Powered Analysis**
   ```python
   ai_result = await self._call_ai_verification(extracted_data)
   # AI analyzes extracted data for:
   # - Logical inconsistencies
   # - Unusual patterns
   # - Missing context
   # - Business rule violations
   ```

   **Step 3: Anomaly Aggregation**
   ```python
   # Combine rule-based and AI-detected anomalies
   # Deduplicate by field + issue
   # Map severity to validation status:
   #   HIGH severity → FAILED
   #   MEDIUM severity → WARNING
   #   LOW severity → WARNING
   ```

4. **AI Verification Prompt**

   **Base Prompt Structure:**
   ```python
   prompt = f"""
   You are a {document_type} verification specialist.
   
   Analyze the following extracted data for anomalies:
   
   {formatted_extracted_data}
   
   Check for:
   1. Missing required fields
   2. Calculation errors
   3. Format inconsistencies
   4. Logical contradictions
   5. Unusual values that may indicate errors
   
   Return JSON with:
   {{
       "is_valid": true/false,
       "confidence_score": 0.0-1.0,
       "summary": "Overall assessment",
       "anomalies": [
           {{
               "field": "field_name",
               "issue": "Description of issue",
               "severity": "high|medium|low",
               "suggestion": "How to fix",
               "expected_value": "...",
               "actual_value": "..."
           }}
       ]
   }}
   """
   ```

5. **Anomaly Severity Mapping**

   **HIGH Severity** → `ValidationStatus.FAILED`
   - Calculation errors
   - Invalid formats (VAT numbers, NI numbers)
   - Missing critical fields
   - Logical contradictions

   **MEDIUM Severity** → `ValidationStatus.WARNING`
   - Unusual but valid values
   - Missing optional but recommended fields
   - Potential issues requiring review

   **LOW Severity** → `ValidationStatus.WARNING`
   - Minor inconsistencies
   - Informational notes

### Why Two-Stage Validation?

- **Rule-Based**: Fast, deterministic, catches obvious errors
- **AI-Based**: Catches subtle issues, understands context, adapts to variations
- **Combined**: Best of both worlds - speed + intelligence

---

## Complete Flow Example: Invoice Processing

### Input
- PDF file: `invoice_2024_001.pdf`
- Content: Standard UK invoice with supplier, customer, line items, VAT

### Step-by-Step Processing

1. **Structure Extraction**
   - Extracts 1 page
   - Finds 1 table (line items)
   - Identifies 15 text blocks
   - Detects header region with company logo

2. **Type Detection**
   - Keywords found: "invoice", "invoice number", "vat", "total"
   - Score: invoice=5, others=0
   - **Result**: `document_type = "invoice"`

3. **Key-Value Extraction**
   - Finds: `"Invoice Number: INV-001"`, `"Date: 15/01/2024"`, `"Total: £1,200.00"`
   - **Result**: 8 key-value pairs with confidence 0.7-0.9

4. **AI Extraction**
   - Sends to GPT-4o with invoice-specific prompt
   - Includes pre-extracted context (key-value pairs, table structure)
   - **Result**: JSON with 20+ fields including line items

5. **Normalization**
   - Merges AI data (priority) + key-value pairs (fill gaps)
   - Flattens nested structures
   - Converts dates to `YYYY-MM-DD`
   - Converts amounts to `Decimal`
   - **Result**: Normalized dict with standard field names

6. **Rule-Based Validation**
   - ✅ Required fields: All present
   - ✅ VAT calculation: £1000 + £200 = £1200 ✓
   - ✅ VAT number format: GB123456789 ✓
   - ✅ VAT rate: 20% (valid) ✓
   - ✅ No duplicates found ✓
   - **Result**: 6 validation results, all PASSED

7. **AI Anomaly Detection**
   - InvoiceVerificationAgent runs
   - Rule checks: All pass
   - AI analysis: "Document appears valid, all calculations correct"
   - **Result**: No anomalies, confidence=0.95

### Final Output
```python
{
    "document_id": 123,
    "status": DocumentStatus.VALIDATED,
    "extracted_data": {
        "invoice_number": "INV-001",
        "invoice_date": "2024-01-15",
        "supplier_name": "Acme Ltd",
        "supplier_vat_number": "GB123456789",
        "net_amount": Decimal("1000.00"),
        "vat_amount": Decimal("200.00"),
        "gross_amount": Decimal("1200.00"),
        "currency": "GBP",
        "line_items": [...]
    },
    "validation_results": [
        ValidationResult(status=PASSED, rule_type=REQUIRED_FIELDS),
        ValidationResult(status=PASSED, rule_type=TOTALS_MATCH),
        ValidationResult(status=PASSED, rule_type=VAT_NUMBER_FORMAT),
        ValidationResult(status=PASSED, rule_type=AI_ANOMALY, confidence=0.95)
    ]
}
```

---

## Key Design Decisions

### 1. Hybrid Extraction (Structure + AI)
**Why?**
- Structure extraction is fast and reliable for simple documents
- AI extraction handles complex layouts and variations
- Combining both improves accuracy and coverage

### 2. Two-Stage Validation (Rules + AI)
**Why?**
- Rule-based validation is deterministic and fast
- AI validation catches edge cases and understands context
- Reduces false positives while maintaining high recall

### 3. Document-Type-Specific Agents
**Why?**
- Each document type has unique validation requirements
- Specialized agents have domain knowledge (e.g., VAT rules, payroll thresholds)
- Better accuracy than generic validation

### 4. Normalization Layer
**Why?**
- AI and structure extraction may use different field names
- Normalization ensures consistent schema for downstream systems
- Handles variations in data structure (nested vs. flat)

### 5. Graceful Degradation
**Why?**
- If AI extraction fails, falls back to structure-based extraction
- If JSON parsing fails, attempts multiple parsing strategies
- System continues to function even with partial failures

---

## Performance Considerations

### Token Management
- PDF text truncated to 15,000 characters for LLM calls
- Prompts optimized to minimize token usage
- Uses `max_tokens=4096` for responses

### Cost Optimization
- Only calls AI when `use_ai=True` flag is set
- Caches document type detection results
- Reuses extracted structure for multiple validations

### Error Handling
- All LLM calls wrapped in try-except
- Returns empty dict on failure (graceful degradation)
- Logs errors for debugging without breaking pipeline

---

## Future Enhancements

1. **Fine-Tuned Models**: Train custom models on domain-specific documents
2. **Streaming Extraction**: Process large documents in chunks
3. **Multi-Modal**: Combine text + image understanding for better accuracy
4. **Active Learning**: Use validation feedback to improve extraction prompts
5. **Confidence Calibration**: Better confidence scores for extracted fields

---

## Summary

The Nova document processing system uses a **sophisticated hybrid approach**:

1. **Structure Extraction** (pdfplumber) → Fast, reliable baseline
2. **AI Extraction** (GPT-4o/Claude) → Handles complexity and variations
3. **Normalization** → Ensures consistent schema
4. **Rule-Based Validation** → Catches obvious errors quickly
5. **AI Anomaly Detection** → Catches subtle issues with context understanding

This architecture provides **high accuracy**, **good performance**, and **graceful degradation** - essential for production financial document processing.
