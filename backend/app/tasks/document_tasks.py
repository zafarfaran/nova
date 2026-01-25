"""Background tasks for document processing."""

import asyncio
import logging
import time
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus, DocumentType
from app.services.pdf_extraction_service import PDFExtractionService
from app.storage import get_storage

logger = logging.getLogger(__name__)


async def process_document(document_id: int, force: bool = False) -> None:
    """Process a document: download, extract data with layout understanding, and update record.

    This task:
    1. Downloads the document from S3
    2. Extracts text with layout and table understanding using pdfplumber
    3. Uses Claude Vision with structured context for comprehensive extraction
    4. Validates extracted data
    5. Updates the document record with extracted data

    Args:
        document_id: ID of the document to process
        force: If True, re-process even if already extracted. Defaults to False.
    """
    db = SessionLocal()
    start_time = time.monotonic()
    try:
        # Get document
        doc = db.get(Document, document_id)
        if not doc:
            logger.error(f"Document {document_id} not found")
            return

        logger.info(
            "Starting extraction for document %s (status=%s, filename=%s, content_type=%s)",
            document_id,
            doc.status,
            doc.filename,
            doc.content_type,
        )

        # Skip if already extracted or validated (unless forced)
        if not force and doc.status in [DocumentStatus.EXTRACTED, DocumentStatus.VALIDATED]:
            logger.info(
                f"Document {document_id} already extracted (status: {doc.status}). "
                "Skipping extraction. Use force=True to re-process."
            )
            return

        # Update status to processing
        doc.status = DocumentStatus.PROCESSING
        db.commit()

        # Download from storage (S3 or UploadThing)
        storage = get_storage()
        try:
            download_start = time.monotonic()
            logger.info(f"Downloading document {document_id} from storage (key: {doc.s3_key[:50]}...)")
            content = storage.download_file(doc.s3_key)
            logger.info(
                "Downloaded %s bytes for document %s in %.2fs",
                len(content),
                document_id,
                time.monotonic() - download_start,
            )
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.processing_error = f"Storage download failed: {str(e)}"
            db.commit()
            logger.error(f"Failed to download document {document_id}: {e}")
            return

        # Determine if this is a PDF - check multiple indicators
        # 1. Content type
        # 2. Filename extension
        # 3. File magic bytes (PDF starts with %PDF)
        is_pdf_by_content_type = doc.content_type == "application/pdf"
        is_pdf_by_extension = doc.filename.lower().endswith(".pdf")
        is_pdf_by_magic = content[:4] == b"%PDF" if len(content) >= 4 else False

        is_pdf = is_pdf_by_content_type or is_pdf_by_extension or is_pdf_by_magic

        logger.info(
            f"Document {document_id} analysis: "
            f"filename='{doc.filename}', content_type='{doc.content_type}', "
            f"is_pdf={is_pdf} (by_type={is_pdf_by_content_type}, by_ext={is_pdf_by_extension}, by_magic={is_pdf_by_magic}), "
            f"size={len(content)} bytes"
        )

        # Get document type hint from existing type
        doc_type_hint = doc.document_type.value.lower() if doc.document_type else None
        logger.info(f"Document type hint: {doc_type_hint or 'none (will auto-detect)'}")

        # Extract data
        extraction_start = time.monotonic()
        try:
            if is_pdf:
                logger.info(f"Using PDF extraction service for document {document_id}...")
                # Use enhanced PDF extraction service for PDFs
                extraction_service = PDFExtractionService()
                extraction_result = await extraction_service.extract(
                    pdf_content=content,
                    document_type=doc_type_hint,
                    use_ai=True,
                )

                # Store the full extraction result
                extracted_data = extraction_result.get("extracted_fields", {})
                extracted_data["_extraction_metadata"] = {
                    "document_structure": extraction_result.get("document_structure"),
                    "tables": extraction_result.get("tables", []),
                    "line_items": extraction_result.get("line_items", []),
                    "confidence": extraction_result.get("confidence", 0.8),
                    "validation": extraction_result.get("validation", {}),
                    "raw_text": extraction_result.get("raw_text", ""),
                }
                extracted_data["detected_document_type"] = extraction_result.get("document_type")

                # Log extraction summary
                validation = extraction_result.get("validation", {})
                logger.info(
                    f"PDF extraction complete for doc {document_id}:\n"
                    f"  - Document type: {extraction_result.get('document_type')}\n"
                    f"  - Confidence: {extraction_result.get('confidence', 'N/A'):.2f}\n"
                    f"  - Tables found: {len(extraction_result.get('tables', []))}\n"
                    f"  - Line items: {len(extraction_result.get('line_items', []))}\n"
                    f"  - Key-value pairs: {len(extraction_result.get('document_structure', {}).get('key_value_pairs', []))}\n"
                    f"  - Validation: valid={validation.get('is_valid')}, issues={len(validation.get('issues', []))}"
                )

                # Log extracted fields
                logger.debug("Extracted fields:")
                for key, value in extracted_data.items():
                    if key != "_extraction_metadata":
                        logger.debug(f"  - {key}: {str(value)[:50]}")

            else:
                # Check if it's an image (OpenAI vision only supports images)
                image_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
                content_type = doc.content_type or "application/octet-stream"

                if content_type in image_types:
                    logger.info(f"Using vision AI extraction for image document {document_id}...")
                    ai_provider = get_ai_provider()
                    logger.info(
                        "AI provider: %s (content_type=%s, size=%s bytes)",
                        ai_provider.__class__.__name__,
                        content_type,
                        len(content),
                    )
                    extracted_data = await ai_provider.extract_document_data(
                        document_content=content,
                        content_type=content_type,
                        filename=doc.filename,
                    )
                    logger.info(
                        "Vision AI extraction complete for doc %s (fields=%s)",
                        document_id,
                        len(extracted_data) if isinstance(extracted_data, dict) else 0,
                    )
                else:
                    # For non-PDF, non-image files, try PDF extraction anyway
                    # (some files might be PDFs with wrong content type)
                    logger.info(f"Attempting PDF extraction for document {document_id} with content_type={content_type}...")
                    try:
                        extraction_service = PDFExtractionService()
                        extraction_result = await extraction_service.extract(
                            pdf_content=content,
                            document_type=doc_type_hint,
                            use_ai=True,
                        )
                        extracted_data = extraction_result.get("extracted_fields", {})
                        extracted_data["_extraction_metadata"] = {
                            "document_structure": extraction_result.get("document_structure"),
                            "tables": extraction_result.get("tables", []),
                            "line_items": extraction_result.get("line_items", []),
                            "confidence": extraction_result.get("confidence", 0.8),
                            "validation": extraction_result.get("validation", {}),
                            "raw_text": extraction_result.get("raw_text", ""),
                        }
                        extracted_data["detected_document_type"] = extraction_result.get("document_type")
                        logger.info(f"PDF extraction succeeded for doc {document_id}")
                    except Exception as pdf_error:
                        logger.warning(f"PDF extraction failed for doc {document_id}: {pdf_error}")
                        # Last resort: return error
                        extracted_data = {
                            "error": f"Unsupported file type: {content_type}",
                            "message": "This file type cannot be processed. Please upload a PDF or image file.",
                        }

            logger.info(
                "Extraction pipeline finished for doc %s in %.2fs",
                document_id,
                time.monotonic() - extraction_start,
            )
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.processing_error = f"Extraction failed: {str(e)}"
            db.commit()
            logger.error(f"Failed to extract data from document {document_id}: {e}", exc_info=True)
            return

        # Normalize extracted data for downstream validators
        normalized_data = _normalize_extracted_data(extracted_data, doc_type_hint)

        # Update document with extracted data
        doc.extracted_data = normalized_data

        extraction_error = None
        if not extracted_data:
            extraction_error = "Extraction returned no data"
        elif isinstance(extracted_data, dict) and extracted_data.get("error"):
            extraction_error = extracted_data.get("error")

        if extraction_error:
            doc.status = DocumentStatus.FAILED
            doc.processing_error = f"Extraction error: {extraction_error}"
            db.commit()
            logger.warning(
                "Document %s marked FAILED due to extraction error: %s",
                document_id,
                extraction_error,
            )
            return

        doc.status = DocumentStatus.EXTRACTED

        # Update key fields based on extracted data
        _update_document_fields(doc, normalized_data)

        db.commit()
        logger.info(
            "Successfully processed document %s (status=%s) in %.2fs",
            document_id,
            doc.status,
            time.monotonic() - start_time,
        )

    except Exception as e:
        logger.error(f"Unexpected error processing document {document_id}: {e}")
        try:
            doc = db.get(Document, document_id)
            if doc:
                doc.status = DocumentStatus.FAILED
                doc.processing_error = f"Unexpected error: {str(e)}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _update_document_fields(doc: Document, extracted_data: dict) -> None:
    """Update document fields from extracted data."""
    # Common fields
    doc.invoice_number = extracted_data.get("invoice_number")
    doc.supplier_name = extracted_data.get("supplier_name") or extracted_data.get("vendor_name")
    doc.supplier_vat_number = extracted_data.get("supplier_vat_number") or extracted_data.get("vendor_vat_number")
    doc.customer_name = extracted_data.get("customer_name") or extracted_data.get("employee_name")
    doc.customer_vat_number = extracted_data.get("customer_vat_number")
    doc.currency = extracted_data.get("currency", "GBP")
    description_value = extracted_data.get("description") or extracted_data.get("summary")
    if isinstance(description_value, (dict, list)):
        try:
            import json

            description_value = json.dumps(description_value)
        except Exception:
            description_value = None
    elif description_value is not None and not isinstance(description_value, str):
        description_value = str(description_value)

    doc.description = description_value


def _normalize_extracted_data(extracted_data: dict, doc_type_hint: str | None) -> dict:
    """Normalize nested extracted data into top-level keys for validators."""
    if not isinstance(extracted_data, dict):
        return extracted_data

    normalized = dict(extracted_data)
    def set_if_missing(key: str, value) -> None:
        if normalized.get(key) is None and value is not None:
            normalized[key] = value

    doc_type = (
        doc_type_hint
        or normalized.get("document_type")
        or normalized.get("detected_document_type")
        or ""
    )
    doc_type = str(doc_type).lower()

    # Common nested details
    for supplier_key in ["supplier", "supplier_details", "vendor", "vendor_details", "seller", "from"]:
        supplier = normalized.get(supplier_key)
        if isinstance(supplier, dict):
            set_if_missing("supplier_name", supplier.get("name") or supplier.get("supplier_name"))
            set_if_missing("supplier_vmvat_number", supplier.get("vat_number"))
            set_if_missing("supplier_vat_number", supplier.get("vat_number") or supplier.get("vat_no"))
            set_if_missing("supplier_address", supplier.get("address"))

    for customer_key in ["customer", "customer_details", "buyer", "bill_to", "client"]:
        customer = normalized.get(customer_key)
        if isinstance(customer, dict):
            set_if_missing("customer_name", customer.get("name") or customer.get("customer_name"))
            set_if_missing("customer_vat_number", customer.get("vat_number") or customer.get("vat_no"))
            set_if_missing("customer_address", customer.get("address"))

    totals = normalized.get("totals") or normalized.get("amounts") or normalized.get("summary")
    if isinstance(totals, dict):
        set_if_missing("net_amount", totals.get("net_amount") or totals.get("subtotal"))
        set_if_missing("vat_amount", totals.get("vat_amount") or totals.get("tax"))
        set_if_missing("gross_amount", totals.get("gross_amount") or totals.get("total"))
        set_if_missing("currency", totals.get("currency"))
        set_if_missing("vat_rate", totals.get("vat_rate"))

    if "bank_statement" in doc_type or doc_type == "bank statement":
        account_details = normalized.get("account_details")
        if isinstance(account_details, dict):
            if not normalized.get("account_number") and account_details.get("account_number"):
                normalized["account_number"] = account_details.get("account_number")
            if not normalized.get("account_holder_name") and account_details.get("account_name"):
                normalized["account_holder_name"] = account_details.get("account_name")
            if not normalized.get("bank_name") and account_details.get("bank_name"):
                normalized["bank_name"] = account_details.get("bank_name")
            if not normalized.get("sort_code") and account_details.get("sort_code"):
                normalized["sort_code"] = account_details.get("sort_code")
            if not normalized.get("iban") and account_details.get("iban"):
                normalized["iban"] = account_details.get("iban")
            if not normalized.get("bic") and account_details.get("bic"):
                normalized["bic"] = account_details.get("bic")

        statement_period = normalized.get("statement_period")
        if isinstance(statement_period, dict):
            if not normalized.get("statement_period_start") and statement_period.get("period_start"):
                normalized["statement_period_start"] = statement_period.get("period_start")
            if not normalized.get("statement_period_end") and statement_period.get("period_end"):
                normalized["statement_period_end"] = statement_period.get("period_end")
            if not normalized.get("statement_date") and statement_period.get("statement_date"):
                normalized["statement_date"] = statement_period.get("statement_date")
            if not normalized.get("period_start") and statement_period.get("period_start"):
                normalized["period_start"] = statement_period.get("period_start")
            if not normalized.get("period_end") and statement_period.get("period_end"):
                normalized["period_end"] = statement_period.get("period_end")

        balances = normalized.get("balances")
        if isinstance(balances, dict):
            if not normalized.get("opening_balance") and balances.get("opening_balance") is not None:
                normalized["opening_balance"] = balances.get("opening_balance")
            if not normalized.get("closing_balance") and balances.get("closing_balance") is not None:
                normalized["closing_balance"] = balances.get("closing_balance")
            if not normalized.get("currency") and balances.get("currency"):
                normalized["currency"] = balances.get("currency")

        summary = (
            normalized.get("summary")
            or normalized.get("transaction_summary")
            or normalized.get("statement_summary")
        )
        if isinstance(summary, dict):
            if not normalized.get("total_credits") and summary.get("total_credits") is not None:
                normalized["total_credits"] = summary.get("total_credits")
            if not normalized.get("total_debits") and summary.get("total_debits") is not None:
                normalized["total_debits"] = summary.get("total_debits")
            if not normalized.get("transaction_count") and summary.get("transaction_count") is not None:
                normalized["transaction_count"] = summary.get("transaction_count")

    if "invoice" in doc_type or "credit_note" in doc_type or "debit_note" in doc_type:
        invoice_details = normalized.get("invoice_details")
        if isinstance(invoice_details, dict):
            set_if_missing("invoice_number", invoice_details.get("invoice_number") or invoice_details.get("invoice_no"))
            set_if_missing("invoice_date", invoice_details.get("invoice_date") or invoice_details.get("date"))
            set_if_missing("due_date", invoice_details.get("due_date"))
        set_if_missing("invoice_number", normalized.get("reference_number"))

    if "receipt" in doc_type:
        vendor = normalized.get("vendor_details") or normalized.get("merchant") or normalized.get("store")
        if isinstance(vendor, dict):
            set_if_missing("vendor_name", vendor.get("vendor_name") or vendor.get("name"))
            set_if_missing("vendor_vat_number", vendor.get("vat_number") or vendor.get("vat_no"))
        receipt_details = normalized.get("receipt_details")
        if isinstance(receipt_details, dict):
            set_if_missing("receipt_date", receipt_details.get("receipt_date") or receipt_details.get("date"))
            set_if_missing("receipt_number", receipt_details.get("receipt_number") or receipt_details.get("reference"))
        if not normalized.get("gross_total") and normalized.get("gross_amount") is not None:
            set_if_missing("gross_total", normalized.get("gross_amount"))

    if "payroll" in doc_type or "payslip" in doc_type:
        employee = normalized.get("employee_details") or normalized.get("employee")
        if isinstance(employee, dict):
            set_if_missing("employee_name", employee.get("employee_name") or employee.get("name"))
            set_if_missing("employee_id", employee.get("employee_id") or employee.get("id"))
            set_if_missing("ni_number", employee.get("ni_number"))
            set_if_missing("tax_code", employee.get("tax_code"))
        pay_period = normalized.get("pay_period") or normalized.get("period")
        if isinstance(pay_period, dict):
            set_if_missing("period_start", pay_period.get("period_start") or pay_period.get("start_date"))
            set_if_missing("period_end", pay_period.get("period_end") or pay_period.get("end_date"))
            set_if_missing("pay_date", pay_period.get("pay_date") or pay_period.get("date"))
        earnings = normalized.get("earnings")
        if isinstance(earnings, dict):
            set_if_missing("basic_pay", earnings.get("basic_pay"))
            set_if_missing("gross_pay", earnings.get("gross_pay") or earnings.get("total"))
        deductions = normalized.get("deductions")
        if isinstance(deductions, dict):
            set_if_missing("paye_tax", deductions.get("paye_tax") or deductions.get("tax"))
            set_if_missing("national_insurance", deductions.get("national_insurance"))
        net_pay = normalized.get("net_pay") or normalized.get("net_amount")
        set_if_missing("net_pay", net_pay)

    if "vat_certificate" in doc_type or "vat registration" in doc_type:
        registration = normalized.get("registration_details")
        if isinstance(registration, dict):
            set_if_missing("vat_number", registration.get("vat_number"))
            set_if_missing("effective_date", registration.get("effective_date"))
            set_if_missing("registration_date", registration.get("registration_date"))
        business = normalized.get("business_details")
        if isinstance(business, dict):
            set_if_missing("business_name", business.get("business_name") or business.get("name"))
            set_if_missing("business_address", business.get("business_address") or business.get("address"))

    if "contract" in doc_type or "agreement" in doc_type:
        contract = normalized.get("contract_details")
        if isinstance(contract, dict):
            set_if_missing("contract_date", contract.get("contract_date") or contract.get("date"))
            set_if_missing("effective_date", contract.get("effective_date"))
        parties = normalized.get("parties")
        if isinstance(parties, list) and parties:
            first_party = parties[0]
            if isinstance(first_party, dict):
                set_if_missing("party_name", first_party.get("name"))

    return normalized

    # Parse date (try multiple field names)
    date_fields = ["invoice_date", "receipt_date", "pay_date", "statement_date", "contract_date"]
    for date_field in date_fields:
        if date_value := extracted_data.get(date_field):
            parsed_date = _parse_date(date_value)
            if parsed_date:
                doc.invoice_date = parsed_date
                break

    # Parse amounts (try multiple field names)
    amount_mappings = {
        "net_amount": ["net_amount", "subtotal", "basic_pay", "gross_pay"],
        "vat_amount": ["vat_amount", "tax", "paye_tax"],
        "gross_amount": ["gross_amount", "gross_total", "total", "net_pay", "closing_balance"],
        "vat_rate": ["vat_rate"],
    }

    for doc_field, possible_keys in amount_mappings.items():
        for key in possible_keys:
            if value := extracted_data.get(key):
                parsed = _parse_decimal(value)
                if parsed is not None:
                    setattr(doc, doc_field, parsed)
                    break

    # Set document type
    if doc_type := extracted_data.get("detected_document_type"):
        try:
            doc.document_type = DocumentType(doc_type.upper())
        except ValueError:
            # Try lowercase
            try:
                doc.document_type = DocumentType(doc_type.lower())
            except ValueError:
                pass


def _parse_date(value: str) -> "datetime.date | None":
    """Parse a date string to date object."""
    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(str(value), fmt).date()
        except (ValueError, TypeError):
            continue

    return None


def _parse_decimal(value) -> "Decimal | None":
    """Parse a value to Decimal."""
    if value is None:
        return None

    try:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            # Remove currency symbols and thousands separators
            import re
            cleaned = re.sub(r"[£$€,\s]", "", value)
            return Decimal(cleaned)
        return Decimal(str(value))
    except Exception:
        return None


def run_process_document(document_id: int) -> None:
    """Sync wrapper for process_document to use with BackgroundTasks."""
    asyncio.run(process_document(document_id))


async def reprocess_failed_documents() -> int:
    """Reprocess all failed documents.

    Returns the number of documents queued for reprocessing.
    """
    db = SessionLocal()
    try:
        from sqlalchemy import select

        stmt = select(Document).where(Document.status == DocumentStatus.FAILED)
        failed_docs = list(db.scalars(stmt).all())

        for doc in failed_docs:
            doc.status = DocumentStatus.PENDING
            doc.processing_error = None
        db.commit()

        # Process each document
        for doc in failed_docs:
            await process_document(doc.id)

        return len(failed_docs)
    finally:
        db.close()
