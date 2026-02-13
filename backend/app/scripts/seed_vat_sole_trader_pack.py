"""Seed script for VAT Sole Trader Pack Request Template.

This script creates:
1. Document types specific to VAT Sole Trader requirements
2. RequestTemplate for "VAT Sole Trader Pack (UK)"
3. RequestTemplateItems with proper descriptions and instructions

Usage:
    python -m app.scripts.seed_vat_sole_trader_pack
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.models.documents.type import DocumentCategory, DocumentType
from app.models.requests.template import RequestTemplate, RequestTemplateItem
from app.models.engagements.engagement import EngagementType


# Document types needed for VAT Sole Trader pack (if they don't exist)
VAT_ST_DOCUMENT_TYPES = [
    {
        "code": "ST_VAT_BANK_STATEMENTS_ALL_ACCOUNTS",
        "name": "Bank Statements - All Accounts (VAT Period)",
        "category_code": "BANKING",
        "requires_account": False,  # Can be any account, including personal
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_SALES_INVOICES",
        "name": "Sales Invoices (VAT)",
        "category_code": "SALES",
        "requires_counterparty": True,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_SALES_POS_SUMMARY",
        "name": "Till/POS Z-Read / Sales Summary",
        "category_code": "SALES",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_SALES_CASHBOOK",
        "name": "Sales Cashbook / Spreadsheet",
        "category_code": "SALES",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_SALES_CREDIT_NOTES_REFUNDS",
        "name": "Sales Credit Notes / Refunds",
        "category_code": "SALES",
        "requires_counterparty": True,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_PURCHASE_INVOICES",
        "name": "Purchase Invoices (VAT)",
        "category_code": "PURCHASES",
        "requires_counterparty": True,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_PURCHASE_CREDIT_NOTES",
        "name": "Purchase Credit Notes",
        "category_code": "PURCHASES",
        "requires_counterparty": True,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_EXPENSE_RECEIPTS_WITH_VAT",
        "name": "Expense Receipts with VAT",
        "category_code": "PURCHASES",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_PROCESSOR_PAYOUT_REPORTS",
        "name": "Payment Processor / Platform Payout Reports",
        "category_code": "SALES",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_CASH_TAKINGS_LOG",
        "name": "Cash Takings Log",
        "category_code": "SALES",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_CARD_STATEMENTS",
        "name": "Card Statements (Business Spending)",
        "category_code": "BANKING",
        "requires_account": True,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_SCHEME_CONFIRMATION",
        "name": "VAT Scheme Confirmation",
        "category_code": "VAT",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_FRS_CALCULATION",
        "name": "Flat Rate Scheme Calculation",
        "category_code": "VAT",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_PIVA_STATEMENT",
        "name": "Postponed Import VAT Statement (PIVA)",
        "category_code": "IMPORT_EXPORT",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_C79_CERTIFICATE",
        "name": "C79 Import VAT Certificate",
        "category_code": "IMPORT_EXPORT",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_ADJUSTMENTS_EVIDENCE",
        "name": "VAT Adjustments Evidence",
        "category_code": "VAT",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_DETAIL_REPORT",
        "name": "VAT Detail Report (From Bookkeeping Software)",
        "category_code": "VAT",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
    {
        "code": "ST_VAT_RETURN_SUMMARY_DRAFT",
        "name": "VAT Return Summary (Draft Box 1-9)",
        "category_code": "VAT",
        "requires_counterparty": False,
        "requires_engagement": True,
    },
]


# Template items for VAT Sole Trader Pack
VAT_ST_TEMPLATE_ITEMS = [
    # Core (always request) - order_index 1-6
    {
        "document_type_code": "ST_VAT_BANK_STATEMENTS_ALL_ACCOUNTS",
        "description": "Upload PDF statements covering [Q_START]–[Q_END] for any account used for business, including personal accounts if you receive/pay business transactions from them.",
        "expected_count": 1,
        "is_required": True,
        "order_index": 1,
    },
    {
        "document_type_code": "ST_VAT_SALES_EVIDENCE_CHOOSE_ONE",
        "description": "Upload one of: Sales invoices (VAT), or Till/POS Z-read / sales summary report, or Spreadsheet cashbook listing daily/weekly sales totals (with VAT breakdown if possible).",
        "expected_count": 1,
        "is_required": True,
        "order_index": 2,
        "note": "This is a 'choose one' group - we'll create separate items for each option",
    },
    {
        "document_type_code": "ST_VAT_SALES_CREDIT_NOTES_REFUNDS",
        "description": "Upload any sales credit notes, refunds reports, or notes of refunds issued in the period.",
        "expected_count": 1,
        "is_required": True,
        "order_index": 3,
    },
    {
        "document_type_code": "ST_VAT_PURCHASE_INVOICES",
        "description": "Upload supplier VAT invoices for purchases in [Q_START]–[Q_END] where you want to reclaim VAT.",
        "expected_count": 1,
        "is_required": True,
        "order_index": 4,
    },
    {
        "document_type_code": "ST_VAT_PURCHASE_CREDIT_NOTES",
        "description": "Upload any supplier credit notes received during the period.",
        "expected_count": 1,
        "is_required": True,
        "order_index": 5,
    },
    {
        "document_type_code": "ST_VAT_EXPENSE_RECEIPTS_WITH_VAT",
        "description": "Upload receipts for VAT-reclaimable expenses (fuel, tools, parking, etc.). Photos are OK if the supplier name/date/total/VAT are readable.",
        "expected_count": 1,
        "is_required": True,
        "order_index": 6,
    },
    # If applicable (common for sole traders) - order_index 7-9
    {
        "document_type_code": "ST_VAT_PROCESSOR_PAYOUT_REPORTS",
        "description": "Upload payout/settlement reports (gross sales, fees, net payout) for the quarter.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 7,
    },
    {
        "document_type_code": "ST_VAT_CASH_TAKINGS_LOG",
        "description": "If you take cash, upload your daily/weekly takings log (even a simple spreadsheet).",
        "expected_count": 1,
        "is_required": False,
        "order_index": 8,
    },
    {
        "document_type_code": "ST_VAT_CARD_STATEMENTS",
        "description": "Upload any card statements covering the quarter used for business expenses.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 9,
    },
    # VAT scheme / adjustments - order_index 10-14
    {
        "document_type_code": "ST_VAT_SCHEME_CONFIRMATION",
        "description": "Tell us which scheme you use. Upload any HMRC letter if you have it.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 10,
    },
    {
        "document_type_code": "ST_VAT_FRS_CALCULATION",
        "description": "Upload your Flat Rate calculation/spreadsheet or your bookkeeping report that shows FRS totals.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 11,
    },
    {
        "document_type_code": "ST_VAT_PIVA_STATEMENT",
        "description": "Upload PIVA statement if importing.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 12,
    },
    {
        "document_type_code": "ST_VAT_C79_CERTIFICATE",
        "description": "Upload C79 certificate if applicable.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 13,
    },
    {
        "document_type_code": "ST_VAT_ADJUSTMENTS_EVIDENCE",
        "description": "Upload workings/evidence for: bad debt relief, partial exemption, fuel scale charge, error corrections, etc.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 14,
    },
    # Optional but very useful - order_index 15-16
    {
        "document_type_code": "ST_VAT_DETAIL_REPORT",
        "description": "Upload VAT detail report from your bookkeeping software if available.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 15,
    },
    {
        "document_type_code": "ST_VAT_RETURN_SUMMARY_DRAFT",
        "description": "Upload draft VAT return summary (Box 1-9) if available.",
        "expected_count": 1,
        "is_required": False,
        "order_index": 16,
    },
]


async def get_or_create_category(session: AsyncSession, code: str, name: str) -> DocumentCategory:
    """Get or create a document category."""
    result = await session.execute(
        select(DocumentCategory).where(DocumentCategory.code == code)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        category = DocumentCategory(code=code, name=name)
        session.add(category)
        await session.flush()
        print(f"  Created category: {name}")
    return category


async def get_or_create_document_type(
    session: AsyncSession, type_data: dict, category: DocumentCategory
) -> DocumentType:
    """Get or create a document type."""
    result = await session.execute(
        select(DocumentType).where(DocumentType.code == type_data["code"])
    )
    doc_type = result.scalar_one_or_none()
    
    if not doc_type:
        doc_type = DocumentType(
            category_id=category.id,
            code=type_data["code"],
            name=type_data["name"],
            client_type_scope="sole_trader",
            requires_counterparty=type_data.get("requires_counterparty", False),
            requires_account=type_data.get("requires_account", False),
            requires_engagement=type_data.get("requires_engagement", True),
            retention_years=6,
            is_active=True,
        )
        session.add(doc_type)
        await session.flush()
        print(f"    Created document type: {type_data['name']}")
    else:
        print(f"    Document type exists: {type_data['name']}")
    
    return doc_type


async def seed_vat_sole_trader_pack(session: AsyncSession) -> None:
    """Seed VAT Sole Trader pack template and document types."""
    print("Seeding VAT Sole Trader Pack...")
    
    # Step 1: Create document types
    print("\n1. Creating document types...")
    doc_type_map = {}
    
    for type_data in VAT_ST_DOCUMENT_TYPES:
        category = await get_or_create_category(
            session, type_data["category_code"], type_data["category_code"].replace("_", " ").title()
        )
        doc_type = await get_or_create_document_type(session, type_data, category)
        doc_type_map[type_data["code"]] = doc_type
    
    # Step 2: Handle "choose one" for sales evidence
    # Create three separate items for the sales evidence options
    sales_evidence_types = [
        ("ST_VAT_SALES_INVOICES", "Sales invoices (VAT)"),
        ("ST_VAT_SALES_POS_SUMMARY", "Till/POS Z-read / sales summary report"),
        ("ST_VAT_SALES_CASHBOOK", "Spreadsheet cashbook listing daily/weekly sales totals"),
    ]
    
    # Create document types for sales evidence if they don't exist
    for code, name in sales_evidence_types:
        if code not in doc_type_map:
            category = await get_or_create_category(session, "SALES", "Sales Documents")
            type_data = {
                "code": code,
                "name": name,
                "category_code": "SALES",
                "requires_counterparty": code == "ST_VAT_SALES_INVOICES",
                "requires_engagement": True,
            }
            doc_type = await get_or_create_document_type(session, type_data, category)
            doc_type_map[code] = doc_type
    
    await session.commit()
    
    # Step 3: Create or update RequestTemplate
    print("\n2. Creating RequestTemplate...")
    result = await session.execute(
        select(RequestTemplate).where(
            RequestTemplate.name == "VAT Sole Trader Pack (UK)",
            RequestTemplate.client_type == "sole_trader",
            RequestTemplate.engagement_type == "vat_return"
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        template = RequestTemplate(
            name="VAT Sole Trader Pack (UK)",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        session.add(template)
        await session.flush()
        print("  Created template: VAT Sole Trader Pack (UK)")
    else:
        print("  Template exists, updating items...")
        # Delete existing items to recreate them
        for item in template.items:
            await session.delete(item)
        await session.flush()
    
    # Step 4: Create template items
    print("\n3. Creating template items...")
    order_index = 0
    
    # Core items (1-6)
    for item_data in VAT_ST_TEMPLATE_ITEMS:
        doc_type_code = item_data["document_type_code"]
        
        # Handle "choose one" for sales evidence
        if doc_type_code == "ST_VAT_SALES_EVIDENCE_CHOOSE_ONE":
            # Create three items, all optional (at least one should be provided)
            for sales_code, sales_name in sales_evidence_types:
                if sales_code in doc_type_map:
                    order_index += 1
                    template_item = RequestTemplateItem(
                        template_id=template.id,
                        document_type_id=doc_type_map[sales_code].id,
                        description=f"Upload {sales_name.lower()} (with VAT breakdown if possible).",
                        expected_count=1,
                        is_required=False,  # At least one of the three should be provided
                        order_index=order_index,
                    )
                    session.add(template_item)
                    print(f"    Created item: {sales_name} (choose one option)")
        else:
            if doc_type_code in doc_type_map:
                order_index += 1
                template_item = RequestTemplateItem(
                    template_id=template.id,
                    document_type_id=doc_type_map[doc_type_code].id,
                    description=item_data["description"],
                    expected_count=item_data["expected_count"],
                    is_required=item_data["is_required"],
                    order_index=order_index,
                )
                session.add(template_item)
                print(f"    Created item: {doc_type_map[doc_type_code].name}")
            else:
                print(f"    WARNING: Document type {doc_type_code} not found, skipping")
    
    await session.commit()
    print("\nVAT Sole Trader Pack seeding complete!")
    print(f"Template ID: {template.id}")
    print(f"Total items: {order_index}")


async def main():
    """Main entry point for the seed script."""
    settings = get_settings()
    
    # Get database URL and convert to async
    db_url = settings.get_database_url()
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Create async engine
    engine = create_async_engine(db_url, echo=False)
    
    # Create session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        await seed_vat_sole_trader_pack(session)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
