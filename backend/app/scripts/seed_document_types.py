"""Seed script for DocumentCategories and DocumentTypes.

This script populates the document_categories and document_types tables
with standard document types for UK VAT compliance for sole traders
and limited companies.

Usage:
    python -m app.scripts.seed_document_types
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.models.document_type import DocumentCategory, DocumentType


# Document categories and their types for UK VAT compliance
DOCUMENT_CATEGORIES = [
    {
        "code": "SALES",
        "name": "Sales Documents",
        "types": [
            {
                "code": "SALES_INVOICE",
                "name": "Sales Invoice",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "CREDIT_NOTE_ISSUED",
                "name": "Credit Note (Issued)",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "DEBIT_NOTE_ISSUED",
                "name": "Debit Note (Issued)",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
        ],
    },
    {
        "code": "PURCHASES",
        "name": "Purchase Documents",
        "types": [
            {
                "code": "PURCHASE_INVOICE",
                "name": "Purchase Invoice",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "CREDIT_NOTE_RECEIVED",
                "name": "Credit Note (Received)",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "DEBIT_NOTE_RECEIVED",
                "name": "Debit Note (Received)",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "EXPENSE_RECEIPT",
                "name": "Expense Receipt",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
        ],
    },
    {
        "code": "BANKING",
        "name": "Banking Documents",
        "types": [
            {
                "code": "BANK_STATEMENT",
                "name": "Bank Statement",
                "requires_counterparty": False,
                "requires_account": True,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "CREDIT_CARD_STATEMENT",
                "name": "Credit Card Statement",
                "requires_counterparty": False,
                "requires_account": True,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "PAYMENT_RECEIPT",
                "name": "Payment Receipt",
                "requires_counterparty": True,
                "requires_account": True,
                "requires_engagement": True,
                "retention_years": 6,
            },
        ],
    },
    {
        "code": "PAYROLL",
        "name": "Payroll Documents",
        "types": [
            {
                "code": "PAYSLIP",
                "name": "Payslip",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "P60",
                "name": "P60 End of Year Certificate",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "P45",
                "name": "P45 Leaving Certificate",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "PENSION_STATEMENT",
                "name": "Pension Statement",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
        ],
    },
    {
        "code": "VAT",
        "name": "VAT Documents",
        "types": [
            {
                "code": "VAT_RETURN",
                "name": "VAT Return",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "VAT_CERTIFICATE",
                "name": "VAT Registration Certificate",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 10,
            },
            {
                "code": "EC_SALES_LIST",
                "name": "EC Sales List",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
        ],
    },
    {
        "code": "CONTRACTS",
        "name": "Contracts & Agreements",
        "types": [
            {
                "code": "SUPPLIER_CONTRACT",
                "name": "Supplier Contract",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 10,
            },
            {
                "code": "CUSTOMER_CONTRACT",
                "name": "Customer Contract",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 10,
            },
            {
                "code": "EMPLOYMENT_CONTRACT",
                "name": "Employment Contract",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 10,
            },
            {
                "code": "LEASE_AGREEMENT",
                "name": "Lease Agreement",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 10,
            },
        ],
    },
    {
        "code": "IMPORT_EXPORT",
        "name": "Import/Export Documents",
        "types": [
            {
                "code": "IMPORT_DECLARATION",
                "name": "Import Declaration (C88)",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "EXPORT_DECLARATION",
                "name": "Export Declaration",
                "requires_counterparty": True,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "CUSTOMS_DUTY_RECEIPT",
                "name": "Customs Duty Receipt",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "INTRASTAT_DECLARATION",
                "name": "Intrastat Declaration",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
        ],
    },
    {
        "code": "COMPANY",
        "name": "Company Documents",
        "types": [
            {
                "code": "CERTIFICATE_OF_INCORPORATION",
                "name": "Certificate of Incorporation",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 99,
            },
            {
                "code": "ARTICLES_OF_ASSOCIATION",
                "name": "Articles of Association",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 99,
            },
            {
                "code": "ANNUAL_RETURN",
                "name": "Annual Return / Confirmation Statement",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 10,
            },
            {
                "code": "BOARD_MINUTES",
                "name": "Board Minutes",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 10,
            },
            {
                "code": "SHARE_CERTIFICATE",
                "name": "Share Certificate",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 99,
            },
        ],
    },
    {
        "code": "TAX",
        "name": "Tax Documents",
        "types": [
            {
                "code": "SELF_ASSESSMENT_RETURN",
                "name": "Self Assessment Tax Return",
                "client_type_scope": "sole_trader",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "CORPORATION_TAX_RETURN",
                "name": "Corporation Tax Return",
                "client_type_scope": "limited_company",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "TAX_CALCULATION",
                "name": "Tax Calculation",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "UTR_LETTER",
                "name": "UTR Letter",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 99,
            },
        ],
    },
    {
        "code": "OTHER",
        "name": "Other Documents",
        "types": [
            {
                "code": "CORRESPONDENCE",
                "name": "General Correspondence",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 3,
            },
            {
                "code": "SUPPORTING_DOCUMENT",
                "name": "Supporting Document",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": True,
                "retention_years": 6,
            },
            {
                "code": "OTHER",
                "name": "Other",
                "requires_counterparty": False,
                "requires_account": False,
                "requires_engagement": False,
                "retention_years": 6,
            },
        ],
    },
]


async def seed_document_types(session: AsyncSession) -> None:
    """Seed document categories and types."""
    print("Seeding document categories and types...")

    for cat_data in DOCUMENT_CATEGORIES:
        # Check if category exists
        result = await session.execute(
            select(DocumentCategory).where(DocumentCategory.code == cat_data["code"])
        )
        category = result.scalar_one_or_none()

        if not category:
            category = DocumentCategory(
                code=cat_data["code"],
                name=cat_data["name"],
            )
            session.add(category)
            await session.flush()
            print(f"  Created category: {cat_data['name']}")
        else:
            print(f"  Category exists: {cat_data['name']}")

        # Create document types for this category
        for type_data in cat_data.get("types", []):
            result = await session.execute(
                select(DocumentType).where(DocumentType.code == type_data["code"])
            )
            doc_type = result.scalar_one_or_none()

            if not doc_type:
                doc_type = DocumentType(
                    category_id=category.id,
                    code=type_data["code"],
                    name=type_data["name"],
                    client_type_scope=type_data.get("client_type_scope"),
                    requires_counterparty=type_data.get("requires_counterparty", False),
                    requires_account=type_data.get("requires_account", False),
                    requires_engagement=type_data.get("requires_engagement", True),
                    retention_years=type_data.get("retention_years", 6),
                    is_active=True,
                )
                session.add(doc_type)
                print(f"    Created type: {type_data['name']}")
            else:
                print(f"    Type exists: {type_data['name']}")

    await session.commit()
    print("Document types seeding complete!")


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
        await seed_document_types(session)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
