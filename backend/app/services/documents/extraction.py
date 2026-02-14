"""PDF extraction service with layout and table understanding.

This service provides comprehensive PDF extraction capabilities:
- Text extraction with layout preservation
- Table detection and structured extraction
- Document structure analysis (headers, sections, key-value pairs)
- Integration with OpenAI GPT-4o for intelligent extraction
"""

import io
import json
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

import pdfplumber
from pdfplumber.page import Page

from app.ai.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class DocumentRegion(Enum):
    """Document region types for layout analysis."""
    HEADER = "header"
    FOOTER = "footer"
    BODY = "body"
    TABLE = "table"
    SIDEBAR = "sidebar"


@dataclass
class TextBlock:
    """Represents a block of text with position information."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int
    font_size: Optional[float] = None
    font_name: Optional[str] = None
    is_bold: bool = False
    region: DocumentRegion = DocumentRegion.BODY


@dataclass
class TableCell:
    """Represents a cell in a table."""
    text: str
    row: int
    col: int
    colspan: int = 1
    rowspan: int = 1


@dataclass
class ExtractedTable:
    """Represents an extracted table with structure."""
    headers: list[str]
    rows: list[list[str]]
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float = 1.0

    def to_dict(self) -> dict:
        """Convert table to dictionary format."""
        return {
            "headers": self.headers,
            "rows": self.rows,
            "page": self.page,
            "position": {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1},
            "confidence": self.confidence,
        }

    def to_records(self) -> list[dict]:
        """Convert table to list of dictionaries (one per row)."""
        if not self.headers:
            return [{"row_data": row} for row in self.rows]
        return [dict(zip(self.headers, row)) for row in self.rows]


@dataclass
class KeyValuePair:
    """Represents a key-value pair extracted from the document."""
    key: str
    value: str
    confidence: float = 1.0
    page: int = 1


@dataclass
class DocumentStructure:
    """Complete extracted document structure."""
    text_blocks: list[TextBlock] = field(default_factory=list)
    tables: list[ExtractedTable] = field(default_factory=list)
    key_value_pairs: list[KeyValuePair] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    metadata: dict = field(default_factory=dict)

    def get_text_by_region(self, region: DocumentRegion) -> str:
        """Get all text from a specific region."""
        return "\n".join(
            block.text for block in self.text_blocks if block.region == region
        )

    def to_llm_context(self) -> str:
        """Convert to formatted context for LLM."""
        sections = []

        # Document metadata
        sections.append("=== DOCUMENT METADATA ===")
        sections.append(f"Pages: {self.page_count}")
        for key, value in self.metadata.items():
            sections.append(f"{key}: {value}")

        # Key-value pairs (likely important document fields)
        if self.key_value_pairs:
            sections.append("\n=== KEY-VALUE PAIRS (Important Fields) ===")
            for kv in self.key_value_pairs:
                sections.append(f"{kv.key}: {kv.value}")

        # Tables
        if self.tables:
            sections.append("\n=== TABLES ===")
            for i, table in enumerate(self.tables, 1):
                sections.append(f"\n--- Table {i} (Page {table.page}) ---")
                if table.headers:
                    sections.append("Headers: " + " | ".join(table.headers))
                sections.append("Data:")
                for row in table.rows:
                    sections.append("  " + " | ".join(str(cell) for cell in row))

        # Full text
        sections.append("\n=== FULL TEXT (Layout Preserved) ===")
        sections.append(self.full_text)

        return "\n".join(sections)


class PDFExtractionService:
    """Service for extracting structured data from PDFs."""

    # Common patterns for key-value extraction
    KEY_VALUE_PATTERNS = [
        # Pattern: "Key: Value" or "Key : Value"
        r"([A-Za-z][A-Za-z\s]+?)[\s]*[:]\s*([^\n]+)",
        # Pattern: "Key Value" where Key is a known field
        r"(Invoice\s*(?:No|Number|#)|Date|Total|VAT|Tax|Amount|Due|Reference|Account)[\s:]*([^\n]+)",
    ]

    # Known document field labels
    KNOWN_FIELDS = {
        "invoice": [
            "invoice number", "invoice no", "invoice #", "inv no", "invoice date",
            "date", "due date", "payment due", "supplier", "vendor", "from",
            "customer", "bill to", "ship to", "net amount", "subtotal", "sub-total",
            "vat", "tax", "gst", "total", "amount due", "balance due",
            "vat number", "vat reg", "tax id", "po number", "purchase order",
            "payment terms", "bank details", "sort code", "account",
        ],
        "bank_statement": [
            "account name", "account number", "sort code", "statement date",
            "statement period", "opening balance", "closing balance",
            "date", "description", "debit", "credit", "balance",
        ],
        "receipt": [
            "receipt", "date", "time", "vendor", "store", "total", "subtotal",
            "tax", "vat", "payment method", "card", "cash", "change",
        ],
        "payroll": [
            "employee", "employee name", "ni number", "national insurance",
            "tax code", "pay period", "pay date", "gross pay", "basic pay",
            "overtime", "bonus", "commission", "paye", "income tax", "tax",
            "national insurance", "ni", "pension", "student loan",
            "net pay", "take home", "deductions", "year to date", "ytd",
        ],
        "vat_certificate": [
            "vat registration", "vat number", "effective date", "business name",
            "trading name", "address", "registration number",
        ],
        "contract": [
            "parties", "effective date", "commencement", "term", "duration",
            "termination", "payment", "services", "obligations", "confidential",
            "governing law", "jurisdiction", "signatures",
        ],
    }

    def __init__(self, ai_provider: OpenAIProvider | None = None):
        """Initialize the PDF extraction service.

        Args:
            ai_provider: Optional AI provider for text-based extraction
        """
        self._ai_provider = ai_provider

    @property
    def ai_provider(self) -> OpenAIProvider:
        """Lazy-load AI provider."""
        if self._ai_provider is None:
            self._ai_provider = OpenAIProvider()
        return self._ai_provider

    async def extract(
        self,
        pdf_content: bytes,
        document_type: str | None = None,
        use_ai: bool = True,
    ) -> dict[str, Any]:
        """Extract structured data from a PDF.

        Args:
            pdf_content: PDF file content as bytes
            document_type: Optional hint for document type (invoice, receipt, etc.)
            use_ai: Whether to use OpenAI GPT-4o for intelligent extraction

        Returns:
            Dictionary containing extracted data with structure:
            {
                "document_structure": DocumentStructure as dict,
                "extracted_fields": document-type-specific fields,
                "tables": list of extracted tables,
                "confidence": extraction confidence score,
                "document_type": detected or provided type,
                "raw_text": full text content,
            }
        """
        logger.info(f"Starting PDF extraction (size: {len(pdf_content)} bytes, type_hint: {document_type})")

        # Step 1: Extract structure using pdfplumber
        logger.info("Step 1/6: Extracting document structure with pdfplumber...")
        structure = self._extract_structure(pdf_content)
        logger.info(
            f"  → Structure extracted: {structure.page_count} pages, "
            f"{len(structure.text_blocks)} text blocks, {len(structure.tables)} tables"
        )

        # Step 2: Detect document type if not provided
        if not document_type:
            logger.info("Step 2/6: Detecting document type...")
            document_type = self._detect_document_type(structure)
            logger.info(f"  → Detected document type: {document_type}")
        else:
            logger.info(f"Step 2/6: Using provided document type: {document_type}")

        # Step 3: Extract key-value pairs based on document type
        logger.info(f"Step 3/6: Extracting key-value pairs for {document_type}...")
        self._extract_key_values(structure, document_type)
        logger.info(f"  → Extracted {len(structure.key_value_pairs)} key-value pairs")
        for kv in structure.key_value_pairs[:5]:  # Log first 5
            logger.debug(f"    - {kv.key}: {kv.value[:50] if len(kv.value) > 50 else kv.value}")
        if len(structure.key_value_pairs) > 5:
            logger.debug(f"    ... and {len(structure.key_value_pairs) - 5} more")

        # Step 4: Use OpenAI GPT-4o for comprehensive extraction
        ai_data = {}
        created_provider = self._ai_provider is None
        if use_ai:
            logger.info("Step 4/6: Running OpenAI GPT-4o extraction...")
            try:
                ai_data = await self._ai_extract(
                    document_type, structure
                )
                logger.info(f"  → AI extraction successful, got {len(ai_data)} fields")
                for key in list(ai_data.keys())[:5]:
                    logger.debug(f"    - {key}: {str(ai_data[key])[:50]}")
            except Exception as e:
                logger.warning(f"  → AI extraction failed: {e}")
            finally:
                if created_provider and self._ai_provider is not None:
                    await self._ai_provider.close()
                    self._ai_provider = None
        else:
            logger.info("Step 4/6: Skipping AI extraction (disabled)")

        # Step 5: Merge and validate results
        logger.info("Step 5/6: Merging extraction results...")
        extracted_fields = self._merge_extractions(
            structure, ai_data, document_type
        )
        logger.info(f"  → Merged result has {len(extracted_fields)} fields")

        # Step 6: Validate extracted data
        logger.info("Step 6/6: Validating extracted data...")
        validation_result = self._validate_extraction(extracted_fields, document_type)
        logger.info(
            f"  → Validation complete: valid={validation_result.get('is_valid')}, "
            f"confidence={validation_result.get('confidence', 0):.2f}, "
            f"issues={len(validation_result.get('issues', []))}"
        )
        for issue in validation_result.get("issues", []):
            logger.warning(f"    - Validation issue: {issue}")

        # Extract line items from tables
        line_items = self._extract_line_items(structure, document_type)
        logger.info(f"Extracted {len(line_items)} line items from tables")

        logger.info(
            f"PDF extraction complete: type={document_type}, "
            f"confidence={validation_result.get('confidence', 0.8):.2f}, "
            f"tables={len(structure.tables)}, line_items={len(line_items)}"
        )

        return {
            "document_structure": {
                "page_count": structure.page_count,
                "metadata": structure.metadata,
                "key_value_pairs": [
                    {"key": kv.key, "value": kv.value, "confidence": kv.confidence}
                    for kv in structure.key_value_pairs
                ],
            },
            "extracted_fields": extracted_fields,
            "tables": [table.to_dict() for table in structure.tables],
            "line_items": line_items,
            "confidence": validation_result.get("confidence", 0.8),
            "document_type": document_type,
            "raw_text": structure.full_text,
            "llm_context": structure.to_llm_context(),
            "validation": validation_result,
        }

    def _extract_structure(self, pdf_content: bytes) -> DocumentStructure:
        """Extract document structure using pdfplumber."""
        structure = DocumentStructure()

        try:
            logger.debug("Opening PDF with pdfplumber...")
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                structure.page_count = len(pdf.pages)
                structure.metadata = pdf.metadata or {}
                logger.debug(f"PDF opened: {structure.page_count} pages, metadata: {list(structure.metadata.keys())}")

                all_text_parts = []

                for page_num, page in enumerate(pdf.pages, 1):
                    logger.debug(f"Processing page {page_num}/{structure.page_count}...")

                    # Extract text blocks with positions
                    text_blocks = self._extract_text_blocks(page, page_num)
                    structure.text_blocks.extend(text_blocks)
                    logger.debug(f"  Page {page_num}: extracted {len(text_blocks)} text blocks")

                    # Extract tables
                    tables = self._extract_tables(page, page_num)
                    structure.tables.extend(tables)
                    if tables:
                        logger.debug(f"  Page {page_num}: found {len(tables)} table(s)")
                        for i, table in enumerate(tables):
                            logger.debug(f"    Table {i+1}: {len(table.headers)} cols, {len(table.rows)} rows")

                    # Get full page text with layout
                    page_text = page.extract_text(layout=True) or ""
                    all_text_parts.append(f"=== Page {page_num} ===\n{page_text}")
                    logger.debug(f"  Page {page_num}: extracted {len(page_text)} chars of text")

                structure.full_text = "\n\n".join(all_text_parts)
                logger.debug(f"Total text extracted: {len(structure.full_text)} chars")

        except Exception as e:
            logger.error(f"Error extracting PDF structure: {e}", exc_info=True)
            structure.metadata["extraction_error"] = str(e)

        return structure

    def _extract_text_blocks(self, page: Page, page_num: int) -> list[TextBlock]:
        """Extract text blocks with position and font information."""
        blocks = []

        try:
            # Extract words with their bounding boxes
            words = page.extract_words(
                keep_blank_chars=True,
                x_tolerance=3,
                y_tolerance=3,
                extra_attrs=["fontname", "size"],
            )

            # Group words into lines
            lines = self._group_words_into_lines(words)

            page_height = page.height
            page_width = page.width

            for line in lines:
                if not line:
                    continue

                text = " ".join(w.get("text", "") for w in line)
                x0 = min(w.get("x0", 0) for w in line)
                y0 = min(w.get("top", 0) for w in line)
                x1 = max(w.get("x1", 0) for w in line)
                y1 = max(w.get("bottom", 0) for w in line)

                # Determine region based on position
                region = self._determine_region(y0, y1, page_height, x0, x1, page_width)

                # Get font info
                font_size = line[0].get("size") if line else None
                font_name = line[0].get("fontname", "") if line else ""
                is_bold = "bold" in font_name.lower() if font_name else False

                blocks.append(TextBlock(
                    text=text.strip(),
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    page=page_num,
                    font_size=font_size,
                    font_name=font_name,
                    is_bold=is_bold,
                    region=region,
                ))

        except Exception as e:
            logger.warning(f"Error extracting text blocks from page {page_num}: {e}")

        return blocks

    def _group_words_into_lines(
        self, words: list[dict], y_tolerance: float = 5
    ) -> list[list[dict]]:
        """Group words into lines based on vertical position."""
        if not words:
            return []

        # Sort by vertical position, then horizontal
        sorted_words = sorted(words, key=lambda w: (w.get("top", 0), w.get("x0", 0)))

        lines = []
        current_line = []
        current_y = None

        for word in sorted_words:
            word_y = word.get("top", 0)

            if current_y is None or abs(word_y - current_y) <= y_tolerance:
                current_line.append(word)
                current_y = word_y if current_y is None else (current_y + word_y) / 2
            else:
                if current_line:
                    # Sort line by x position
                    current_line.sort(key=lambda w: w.get("x0", 0))
                    lines.append(current_line)
                current_line = [word]
                current_y = word_y

        if current_line:
            current_line.sort(key=lambda w: w.get("x0", 0))
            lines.append(current_line)

        return lines

    def _determine_region(
        self,
        y0: float,
        y1: float,
        page_height: float,
        x0: float,
        x1: float,
        page_width: float,
    ) -> DocumentRegion:
        """Determine the document region based on position."""
        # Header: top 15% of page
        if y1 < page_height * 0.15:
            return DocumentRegion.HEADER

        # Footer: bottom 10% of page
        if y0 > page_height * 0.90:
            return DocumentRegion.FOOTER

        # Sidebar: far left or right 15%
        if x1 < page_width * 0.15 or x0 > page_width * 0.85:
            return DocumentRegion.SIDEBAR

        return DocumentRegion.BODY

    def _extract_tables(self, page: Page, page_num: int) -> list[ExtractedTable]:
        """Extract tables from a page."""
        tables = []

        try:
            # Find tables
            found_tables = page.find_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3,
                    "join_tolerance": 3,
                }
            )

            for table in found_tables:
                try:
                    extracted = table.extract()
                    if not extracted or len(extracted) < 2:
                        continue

                    # First row as headers (clean them up)
                    headers = [
                        self._clean_cell(cell) for cell in extracted[0]
                    ]

                    # Remaining rows as data
                    rows = [
                        [self._clean_cell(cell) for cell in row]
                        for row in extracted[1:]
                    ]

                    # Get bounding box
                    bbox = table.bbox

                    tables.append(ExtractedTable(
                        headers=headers,
                        rows=rows,
                        page=page_num,
                        x0=bbox[0],
                        y0=bbox[1],
                        x1=bbox[2],
                        y1=bbox[3],
                        confidence=0.9 if all(headers) else 0.7,
                    ))
                except Exception as e:
                    logger.warning(f"Error extracting table: {e}")

        except Exception as e:
            logger.warning(f"Error finding tables on page {page_num}: {e}")

        return tables

    def _clean_cell(self, cell: Any) -> str:
        """Clean a table cell value."""
        if cell is None:
            return ""
        text = str(cell).strip()
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        return text

    def _detect_document_type(self, structure: DocumentStructure) -> str:
        """Detect document type from structure."""
        text_lower = structure.full_text.lower()
        logger.debug(f"Detecting document type from {len(text_lower)} chars of text")

        # Score each document type
        scores = {}

        for doc_type, keywords in self.KNOWN_FIELDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[doc_type] = score
            if score > 0:
                logger.debug(f"  {doc_type}: score={score}")

        # Return highest scoring type
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
            logger.debug(f"Best match: {best_type} (score={best_score})")
            if best_score >= 3:  # Minimum threshold
                logger.info(f"Document type detected by keyword scoring: {best_type}")
                return best_type

        # Check for specific indicators
        if "invoice" in text_lower or "inv no" in text_lower:
            logger.info("Document type detected by indicator: invoice")
            return "invoice"
        if "statement" in text_lower and "bank" in text_lower:
            logger.info("Document type detected by indicator: bank_statement")
            return "bank_statement"
        if "receipt" in text_lower:
            logger.info("Document type detected by indicator: receipt")
            return "receipt"
        if "payslip" in text_lower or "payroll" in text_lower:
            logger.info("Document type detected by indicator: payroll")
            return "payroll"

        logger.info("Document type could not be determined, defaulting to 'other'")
        return "other"

    def _extract_key_values(
        self, structure: DocumentStructure, document_type: str
    ) -> None:
        """Extract key-value pairs from the document."""
        text = structure.full_text

        # Get relevant fields for this document type
        relevant_fields = self.KNOWN_FIELDS.get(document_type, [])

        # Pattern-based extraction
        for pattern in self.KEY_VALUE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                key = match.group(1).strip().lower()
                value = match.group(2).strip()

                if value and len(value) < 200:  # Sanity check
                    # Check if this is a relevant field
                    is_relevant = any(
                        field in key for field in relevant_fields
                    )
                    confidence = 0.9 if is_relevant else 0.7

                    structure.key_value_pairs.append(KeyValuePair(
                        key=key,
                        value=value,
                        confidence=confidence,
                    ))

        # Also extract from text blocks that look like key-value pairs
        for block in structure.text_blocks:
            if ":" in block.text:
                parts = block.text.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()

                    if key and value and len(value) < 200:
                        # Avoid duplicates
                        existing_keys = [kv.key for kv in structure.key_value_pairs]
                        if key not in existing_keys:
                            structure.key_value_pairs.append(KeyValuePair(
                                key=key,
                                value=value,
                                confidence=0.8,
                                page=block.page,
                            ))

    async def _ai_extract(
        self,
        document_type: str,
        structure: DocumentStructure,
    ) -> dict[str, Any]:
        """Use OpenAI GPT-4o for comprehensive text-based extraction."""
        logger.debug(f"Preparing AI extraction for document type: {document_type}")

        # Build context-aware prompt with extracted text
        prompt = self._build_extraction_prompt(document_type, structure)
        logger.debug(f"Built extraction prompt ({len(prompt)} chars)")

        # Add the full extracted text to the prompt
        full_prompt = f"""{prompt}

=== DOCUMENT TEXT ===
{structure.full_text[:15000]}
"""
        logger.debug(f"Full prompt length: {len(full_prompt)} chars")

        try:
            logger.info(f"Calling OpenAI API (model: {self.ai_provider.model})...")
            response = await self.ai_provider.client.chat.completions.create(
                model=self.ai_provider.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document data extraction specialist. Extract structured data from documents accurately. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": full_prompt,
                    }
                ],
                max_tokens=4096,
                temperature=0.1,  # Low temperature for more consistent extraction
            )

            response_text = response.choices[0].message.content or ""
            logger.debug(f"Received response from OpenAI ({len(response_text)} chars)")
            logger.debug(f"Response preview: {response_text[:200]}...")

            result = self._extract_json(response_text)
            logger.info(f"Successfully parsed JSON response with {len(result)} fields")
            return result

        except Exception as e:
            logger.error(f"AI extraction error: {e}", exc_info=True)
            return {}

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from response text."""
        # Try to parse as-is first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in text
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse JSON from response: {text[:200]}...")
        return {}

    def _build_extraction_prompt(
        self, document_type: str, structure: DocumentStructure
    ) -> str:
        """Build a context-aware extraction prompt."""
        base_prompts = {
            "invoice": self._get_invoice_prompt(),
            "bank_statement": self._get_bank_statement_prompt(),
            "receipt": self._get_receipt_prompt(),
            "payroll": self._get_payroll_prompt(),
            "vat_certificate": self._get_vat_certificate_prompt(),
            "contract": self._get_contract_prompt(),
        }

        prompt = base_prompts.get(document_type, self._get_generic_prompt())

        # Add context from structure analysis
        context_parts = [
            f"\n\n=== PRE-EXTRACTED CONTEXT ===",
            f"Document has {structure.page_count} page(s).",
        ]

        if structure.tables:
            context_parts.append(f"Found {len(structure.tables)} table(s).")

        if structure.key_value_pairs:
            context_parts.append("Pre-extracted key-value pairs:")
            for kv in structure.key_value_pairs[:10]:  # Limit to avoid token overflow
                context_parts.append(f"  - {kv.key}: {kv.value}")

        context_parts.append(
            "\nUse this context to validate and enhance your extraction. "
            "If the pre-extracted values conflict with what you see, "
            "prefer the values you can directly observe in the document."
        )

        return prompt + "\n".join(context_parts)

    def _get_invoice_prompt(self) -> str:
        """Get invoice extraction prompt."""
        return """Analyze this invoice document and extract all information in JSON format.

REQUIRED FIELDS:
- invoice_number: The invoice number/reference
- invoice_date: Date (YYYY-MM-DD format)
- due_date: Payment due date if shown (YYYY-MM-DD)
- supplier_name: Name of supplier/vendor
- supplier_address: Full address if shown
- supplier_vat_number: VAT registration number (UK format: GB + 9/12 digits)
- customer_name: Name of customer
- customer_address: Full address if shown
- customer_vat_number: Customer VAT number if shown

FINANCIAL FIELDS:
- currency: Currency code (GBP, EUR, USD, etc.)
- net_amount: Net amount before VAT (numeric only)
- vat_amount: VAT amount (numeric only)
- vat_rate: VAT rate as percentage (e.g., 20)
- gross_amount: Total including VAT (numeric only)

LINE ITEMS (extract as array):
- line_items: [
    {
        "description": "item description",
        "quantity": number,
        "unit_price": number,
        "vat_rate": number,
        "net_total": number,
        "vat_amount": number,
        "gross_total": number
    }
]

ADDITIONAL FIELDS:
- payment_terms: Payment terms if mentioned
- bank_details: Bank account details if shown
- po_number: Purchase order reference
- notes: Any additional notes

Return ONLY valid JSON. Set missing fields to null."""

    def _get_bank_statement_prompt(self) -> str:
        """Get bank statement extraction prompt."""
        return """Analyze this bank statement and extract all information in JSON format.

ACCOUNT DETAILS:
- account_name: Name on the account
- account_number: Full or partial account number
- sort_code: Bank sort code (format: XX-XX-XX)
- bank_name: Name of the bank
- iban: IBAN if shown
- bic: BIC/SWIFT code if shown

STATEMENT PERIOD:
- statement_date: Statement generation date (YYYY-MM-DD)
- period_start: Start of statement period (YYYY-MM-DD)
- period_end: End of statement period (YYYY-MM-DD)

BALANCES:
- opening_balance: Opening balance (numeric, negative if overdrawn)
- closing_balance: Closing balance (numeric)
- currency: Currency code

TRANSACTIONS (extract ALL transactions as array):
- transactions: [
    {
        "date": "YYYY-MM-DD",
        "description": "transaction description",
        "reference": "reference if shown",
        "type": "credit" or "debit",
        "amount": number (positive value),
        "balance": running balance after transaction
    }
]

SUMMARY:
- total_credits: Sum of all credits
- total_debits: Sum of all debits
- transaction_count: Number of transactions

Return ONLY valid JSON. Set missing fields to null."""

    def _get_receipt_prompt(self) -> str:
        """Get receipt extraction prompt."""
        return """Analyze this receipt and extract all information in JSON format.

VENDOR DETAILS:
- vendor_name: Store/business name
- vendor_address: Address if shown
- vendor_phone: Phone number if shown
- vendor_vat_number: VAT number if shown

TRANSACTION DETAILS:
- receipt_date: Date (YYYY-MM-DD)
- receipt_time: Time if shown (HH:MM)
- receipt_number: Receipt/transaction number
- till_number: Till/register number if shown
- cashier: Cashier name/ID if shown

ITEMS (extract ALL items):
- items: [
    {
        "description": "item name",
        "quantity": number,
        "unit_price": number,
        "total": number,
        "vat_rate": percentage if shown
    }
]

TOTALS:
- subtotal: Subtotal before tax
- vat_amount: VAT/tax amount
- vat_rate: VAT rate percentage
- gross_total: Total amount paid
- currency: Currency code

PAYMENT:
- payment_method: cash/card/other
- card_type: Visa/Mastercard/etc if card payment
- card_last_four: Last 4 digits if shown
- amount_tendered: Amount given (for cash)
- change: Change given (for cash)

Return ONLY valid JSON. Set missing fields to null."""

    def _get_payroll_prompt(self) -> str:
        """Get payroll extraction prompt."""
        return """Analyze this payroll/payslip document and extract all information in JSON format.

EMPLOYEE DETAILS:
- employee_name: Full name
- employee_id: Employee number/ID
- ni_number: National Insurance number (format: AB123456C)
- tax_code: Current tax code (e.g., 1257L)
- department: Department if shown
- job_title: Job title if shown

PAY PERIOD:
- pay_period: Description (e.g., "Month 9", "Week 34")
- pay_date: Payment date (YYYY-MM-DD)
- period_start: Start of pay period
- period_end: End of pay period

EARNINGS (extract all):
- basic_pay: Basic salary amount
- overtime: Overtime pay
- bonus: Bonus amount
- commission: Commission
- other_earnings: [
    {"description": "name", "amount": number}
]
- gross_pay: Total gross pay

DEDUCTIONS:
- paye_tax: Income tax (PAYE)
- national_insurance: Employee NI
- pension_employee: Employee pension contribution
- student_loan: Student loan deduction
- other_deductions: [
    {"description": "name", "amount": number}
]
- total_deductions: Total deductions

NET PAY:
- net_pay: Take-home pay

YEAR TO DATE (if shown):
- ytd_gross: Year-to-date gross
- ytd_tax: Year-to-date tax paid
- ytd_ni: Year-to-date NI paid
- ytd_pension: Year-to-date pension

EMPLOYER CONTRIBUTIONS (if shown):
- employer_ni: Employer NI contribution
- employer_pension: Employer pension contribution

Return ONLY valid JSON. Set missing fields to null."""

    def _get_vat_certificate_prompt(self) -> str:
        """Get VAT certificate extraction prompt."""
        return """Analyze this VAT registration certificate and extract all information in JSON format.

REGISTRATION DETAILS:
- vat_number: VAT registration number
- effective_date: Registration effective date (YYYY-MM-DD)
- registration_date: Date certificate issued

BUSINESS DETAILS:
- business_name: Registered business name
- trading_name: Trading name if different
- business_address: Full registered address
- business_type: Type of business entity

VAT SCHEME:
- vat_scheme: Scheme type (Standard, Flat Rate, etc.)
- accounting_period: VAT return period
- stagger_code: HMRC stagger code if shown

Return ONLY valid JSON. Set missing fields to null."""

    def _get_contract_prompt(self) -> str:
        """Get contract extraction prompt."""
        return """Analyze this contract/agreement and extract all information in JSON format.

CONTRACT DETAILS:
- contract_type: Type of contract (service, employment, etc.)
- contract_title: Title of the agreement
- contract_date: Date of contract (YYYY-MM-DD)
- effective_date: When contract takes effect

PARTIES:
- parties: [
    {
        "name": "party name",
        "role": "client/provider/employer/employee/etc.",
        "address": "address if shown",
        "registration_number": "company number if shown"
    }
]

TERMS:
- start_date: Contract start date
- end_date: Contract end date or "ongoing"
- term_length: Duration description
- notice_period: Notice period for termination
- renewal_terms: Auto-renewal terms if specified

FINANCIAL TERMS:
- total_value: Total contract value
- payment_amount: Regular payment amount
- payment_frequency: weekly/monthly/annually/etc.
- payment_terms: Payment terms description
- currency: Currency code

VAT TREATMENT:
- vat_applicable: true/false
- vat_rate: VAT rate if applicable

KEY CLAUSES:
- termination_clause: Summary of termination terms
- confidentiality: true/false if confidentiality clause exists
- non_compete: true/false if non-compete clause exists

Return ONLY valid JSON. Set missing fields to null."""

    def _get_generic_prompt(self) -> str:
        """Get generic extraction prompt."""
        return """Analyze this document and extract all relevant information in JSON format.

Identify and extract:
1. Document type and purpose
2. All dates mentioned
3. All monetary amounts with context
4. All names (people, companies, organizations)
5. All reference numbers
6. Any tables and their contents
7. Key terms and conditions
8. Contact information

Structure the output as:
{
    "document_type": "detected type",
    "title": "document title if identifiable",
    "date": "primary date",
    "parties": ["list of parties/names involved"],
    "reference_numbers": {"type": "number"},
    "amounts": [{"description": "what", "amount": number, "currency": "code"}],
    "key_information": {"field": "value"},
    "tables": [{"headers": [], "rows": [[]]}],
    "summary": "brief summary of document"
}

Return ONLY valid JSON. Set missing fields to null."""

    def _merge_extractions(
        self,
        structure: DocumentStructure,
        vision_data: dict[str, Any],
        document_type: str,
    ) -> dict[str, Any]:
        """Merge structure-based and vision-based extractions."""
        # Start with vision data as base (usually more accurate)
        merged = dict(vision_data) if vision_data else {}

        # Build map from structure key-values
        structure_kv = {kv.key: kv.value for kv in structure.key_value_pairs}

        # Fill in missing fields from structure extraction
        for key, value in structure_kv.items():
            # Normalize key
            normalized_key = key.replace(" ", "_").lower()

            # Only add if not already present in vision data
            if normalized_key not in merged or merged.get(normalized_key) is None:
                merged[normalized_key] = value

        # Ensure document type is set
        merged["document_type"] = document_type

        return merged

    def _extract_line_items(
        self, structure: DocumentStructure, document_type: str
    ) -> list[dict]:
        """Extract line items from tables based on document type."""
        line_items = []

        if document_type not in ["invoice", "receipt"]:
            return line_items

        for table in structure.tables:
            # Check if this looks like a line items table
            headers_lower = [h.lower() for h in table.headers]

            # Look for indicators of line item tables
            is_line_items = any(
                indicator in " ".join(headers_lower)
                for indicator in ["description", "qty", "quantity", "price", "amount", "total", "item"]
            )

            if is_line_items:
                for row in table.rows:
                    if len(row) >= 2:  # Need at least description and amount
                        item = dict(zip(table.headers, row))
                        line_items.append(item)

        return line_items

    def _validate_extraction(
        self, extracted: dict[str, Any], document_type: str
    ) -> dict[str, Any]:
        """Validate extracted data."""
        logger.debug(f"Validating extraction for document type: {document_type}")
        issues = []
        confidence = 1.0

        # Required fields by document type
        required_fields = {
            "invoice": ["invoice_number", "invoice_date", "gross_amount"],
            "bank_statement": ["account_number", "period_start", "closing_balance"],
            "receipt": ["vendor_name", "receipt_date", "gross_total"],
            "payroll": ["employee_name", "gross_pay", "net_pay"],
        }

        # Check required fields
        required = required_fields.get(document_type, [])
        logger.debug(f"Checking {len(required)} required fields: {required}")
        for field in required:
            value = extracted.get(field)
            if not value:
                issues.append(f"Missing required field: {field}")
                confidence -= 0.1
                logger.debug(f"  ✗ {field}: MISSING")
            else:
                logger.debug(f"  ✓ {field}: {str(value)[:30]}")

        # Validate calculations for invoices
        if document_type == "invoice":
            logger.debug("Validating invoice calculations...")
            net = self._to_decimal(extracted.get("net_amount"))
            vat = self._to_decimal(extracted.get("vat_amount"))
            gross = self._to_decimal(extracted.get("gross_amount"))
            logger.debug(f"  net={net}, vat={vat}, gross={gross}")

            if net and vat and gross:
                expected_gross = net + vat
                diff = abs(expected_gross - gross)
                logger.debug(f"  Calculation: {net} + {vat} = {expected_gross} (actual: {gross}, diff: {diff})")
                if diff > Decimal("0.02"):
                    issues.append(
                        f"Calculation mismatch: {net} + {vat} = {expected_gross}, "
                        f"but gross is {gross}"
                    )
                    confidence -= 0.15
                    logger.warning(f"Invoice calculation mismatch: expected {expected_gross}, got {gross}")

        # Validate payroll calculations
        if document_type == "payroll":
            logger.debug("Validating payroll calculations...")
            gross = self._to_decimal(extracted.get("gross_pay"))
            net = self._to_decimal(extracted.get("net_pay"))
            tax = self._to_decimal(extracted.get("paye_tax")) or Decimal("0")
            ni = self._to_decimal(extracted.get("national_insurance")) or Decimal("0")
            logger.debug(f"  gross={gross}, net={net}, tax={tax}, ni={ni}")

            if gross and net:
                if net > gross:
                    issues.append("Net pay exceeds gross pay")
                    confidence -= 0.2
                    logger.warning(f"Payroll validation error: net ({net}) > gross ({gross})")

        # Ensure confidence is in valid range
        confidence = max(0.1, min(1.0, confidence))

        logger.info(
            f"Validation complete: is_valid={len(issues) == 0}, "
            f"confidence={confidence:.2f}, issues={len(issues)}"
        )

        return {
            "is_valid": len(issues) == 0,
            "confidence": confidence,
            "issues": issues,
        }

    def _to_decimal(self, value: Any) -> Decimal | None:
        """Convert value to Decimal."""
        if value is None:
            return None
        try:
            if isinstance(value, Decimal):
                return value
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            if isinstance(value, str):
                cleaned = re.sub(r"[£$€,\s]", "", value)
                return Decimal(cleaned)
            return None
        except Exception:
            return None
