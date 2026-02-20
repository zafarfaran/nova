#!/usr/bin/env python3
"""Test script to send all email types to verify email templates and wordings.

Usage:
    python test_emails.py your-email@example.com
"""

import asyncio
import sys
from datetime import datetime, timedelta

from app.ai import get_ai_provider
from app.schemas.email import EmailPurpose, EmailRequest, EmailTone
from app.services.email import EmailService


async def send_test_emails(test_email: str):
    """Send all email types to the test email address.

    Args:
        test_email: Email address to send test emails to
    """
    print(f"🚀 Sending test emails to: {test_email}")
    print("-" * 60)

    # Initialize services without database (not needed for email testing)
    ai_provider = get_ai_provider()

    # Create a mock db session - emails don't actually need database
    class MockDB:
        def get(self, model, id):
            return None

    db = MockDB()
    email_service = EmailService(db=db, ai_provider=ai_provider)

    test_emails = []

    # 1. Welcome Email
    print("\n📧 1. Sending Welcome Email...")
    welcome_email = EmailRequest(
        to_email=test_email,
        to_name="Sarah Mitchell",
        purpose=EmailPurpose.WELCOME,
        tone=EmailTone.FRIENDLY,
        context_data={
            "company_name": "Mitchell & Associates",
            "contact_name": "Sarah Mitchell",
            "vat_scheme": "standard",
            "entity_type": "limited company",
            "onboarding_url": "https://nova.app/client/123/dashboard",
            "steps": [
                "1. Click the link below to access your Nova dashboard",
                "2. Review your VAT period and document checklist",
                "3. Upload your documents in bulk - Nova handles hundreds in seconds",
                "4. Watch Nova's AI automatically validate and categorize everything",
                "5. Review any flagged items (if any) and make corrections",
                "6. Submit for final review - done in minutes, not hours"
            ],
            "required_documents": [
                "Bank statements for the VAT period",
                "Sales invoices and credit notes",
                "Purchase invoices and receipts",
                "Payroll records (if applicable)",
                "Any other relevant VAT documentation"
            ],
            "benefits": [
                "Process thousands of documents in seconds with Claude AI",
                "99.9% accuracy with automated validation and compliance checking",
                "Real-time bank sync and reconciliation",
                "Smart anomaly detection that catches errors before they happen",
                "One-click VAT return generation",
                "Save 95% of your time on VAT compliance"
            ],
            "support_info": "If you have any questions, simply reply to this email or contact our support team.",
        }
    )
    test_emails.append(("Welcome Email", welcome_email))

    # 2. Validation Issues Email
    print("📧 2. Sending Validation Issues Email...")
    validation_email = EmailRequest(
        to_email=test_email,
        to_name="James Chen",
        purpose=EmailPurpose.VALIDATION_ISSUES,
        tone=EmailTone.PROFESSIONAL,
        context_data={
            "document_name": "January_Bank_Statement.pdf",
            "document_type": "bank statement",
            "issues": [
                "❌ VAT number format is invalid (should be GB followed by 9 or 12 digits)",
                "⚠️ Invoice date is outside the VAT period",
                "❌ Total amount doesn't match the sum of line items"
            ],
            "issue_count": 3,
            "vat_period": "Q1 2026",
            "call_to_action": "Upload the corrected document and Nova will re-validate it instantly.",
        }
    )
    test_emails.append(("Validation Issues Email", validation_email))

    # 3. Document Rejection Email
    print("📧 3. Sending Document Rejection Email...")
    rejection_email = EmailRequest(
        to_email=test_email,
        to_name="Emma Thompson",
        subject="Document Rejected: Q4_Expenses.xlsx",
        purpose=EmailPurpose.VALIDATION_ISSUES,
        tone=EmailTone.PROFESSIONAL,
        context_data={
            "document_name": "Q4_Expenses.xlsx",
            "document_type": "expense report",
            "rejected_by": "Michael Brown (Senior Accountant)",
            "rejection_reason": "The expense categories don't match our standard chart of accounts. Please re-categorize using the categories provided in the template and ensure all receipts are included.",
            "vat_period": "Q4 2025",
            "call_to_action": "Upload the corrected document to your Nova dashboard.",
        }
    )
    test_emails.append(("Document Rejection Email", rejection_email))

    # 4. Missing Documents Email
    print("📧 4. Sending Missing Documents Email...")
    missing_docs_email = EmailRequest(
        to_email=test_email,
        to_name="David Wilson",
        purpose=EmailPurpose.MISSING_DOCUMENTS,
        tone=EmailTone.PROFESSIONAL,
        context_data={
            "missing_items": [
                "Bank statement for December 2025",
                "Sales invoices for the period",
                "Petty cash receipts",
                "Credit card statements"
            ],
            "missing_count": 4,
            "due_date": "February 7, 2026",
            "call_to_action": "Upload the missing documents and Nova will process them instantly.",
        }
    )
    test_emails.append(("Missing Documents Email", missing_docs_email))

    # 5. VAT Return Ready Email
    print("📧 5. Sending VAT Return Ready Email...")
    vat_ready_email = EmailRequest(
        to_email=test_email,
        to_name="Lisa Anderson",
        purpose=EmailPurpose.VAT_RETURN_READY,
        tone=EmailTone.PROFESSIONAL,
        context_data={
            "vat_period": "Q4 2025",
            "period_start": "2025-10-01",
            "period_end": "2025-12-31",
            "due_date": "2026-02-07",
            "call_to_action": "Review your VAT return in Nova - ready for submission in one click.",
        }
    )
    test_emails.append(("VAT Return Ready Email", vat_ready_email))

    # 6. Reminder Email
    print("📧 6. Sending Reminder Email...")
    reminder_email = EmailRequest(
        to_email=test_email,
        to_name="Robert Taylor",
        purpose=EmailPurpose.REMINDER,
        tone=EmailTone.FRIENDLY,
        context_data={
            "reminder_type": "VAT deadline approaching",
            "days_remaining": 5,
            "deadline_date": "February 7, 2026",
            "pending_tasks": [
                "Upload December bank statements",
                "Review and approve VAT return",
                "Submit to HMRC"
            ],
            "call_to_action": "Complete these tasks in your Nova dashboard to stay on track.",
        }
    )
    test_emails.append(("Reminder Email", reminder_email))

    # 7. Invoice Request Email
    print("📧 7. Sending Invoice Request Email...")
    invoice_request_email = EmailRequest(
        to_email=test_email,
        to_name="Jennifer Martinez",
        purpose=EmailPurpose.INVOICE_REQUEST,
        tone=EmailTone.PROFESSIONAL,
        context_data={
            "requested_invoices": [
                "Invoice #2025-1234 dated November 15, 2025",
                "Invoice #2025-1267 dated December 3, 2025",
                "Any missing receipts for expenses over £50"
            ],
            "reason": "to complete the VAT return for Q4 2025",
            "due_date": "February 3, 2026",
            "call_to_action": "Upload these invoices to Nova and we'll automatically extract and validate all the details.",
        }
    )
    test_emails.append(("Invoice Request Email", invoice_request_email))

    # 8. Follow-up Email
    print("📧 8. Sending Follow-up Email...")
    followup_email = EmailRequest(
        to_email=test_email,
        to_name="Christopher Lee",
        purpose=EmailPurpose.FOLLOW_UP,
        tone=EmailTone.FRIENDLY,
        context_data={
            "previous_request": "missing bank statements for Q4 2025",
            "days_since_request": 3,
            "original_due_date": "January 31, 2026",
            "new_due_date": "February 5, 2026",
            "call_to_action": "Upload the documents when you have a moment - Nova will process them in seconds.",
        }
    )
    test_emails.append(("Follow-up Email", followup_email))

    # 9. General Communication Email
    print("📧 9. Sending General Communication Email...")
    general_email = EmailRequest(
        to_email=test_email,
        to_name="Patricia Garcia",
        purpose=EmailPurpose.GENERAL,
        tone=EmailTone.PROFESSIONAL,
        context_data={
            "subject_matter": "New features available in Nova",
            "message": "We've added new AI-powered features to help you work even faster",
            "features": [
                "Real-time bank transaction sync with all major UK banks",
                "Enhanced anomaly detection that catches duplicate invoices",
                "Automated email reminders for your clients",
                "One-click export to your accounting software"
            ],
            "call_to_action": "Log in to Nova to explore the new features.",
        }
    )
    test_emails.append(("General Communication Email", general_email))

    # Send all emails
    print("\n" + "=" * 60)
    print("Sending emails...")
    print("=" * 60)

    results = []
    for name, email_request in test_emails:
        try:
            response = await email_service.send_email(email_request)
            if response.success:
                print(f"✅ {name}: Sent successfully")
                if response.generated_subject:
                    print(f"   Subject: {response.generated_subject}")
                results.append((name, "SUCCESS", response.message))
            else:
                print(f"❌ {name}: Failed - {response.message}")
                results.append((name, "FAILED", response.message))
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
            results.append((name, "ERROR", str(e)))

        # Small delay between emails
        await asyncio.sleep(1)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    success_count = sum(1 for _, status, _ in results if status == "SUCCESS")
    total_count = len(results)

    print(f"\nTotal emails: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")

    print(f"\n✅ All test emails have been sent to {test_email}")
    print("Check your inbox to review the wordings and templates!")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_emails.py <your-email@example.com>")
        print("\nExample:")
        print("  python test_emails.py sarah@example.com")
        sys.exit(1)

    test_email = sys.argv[1]

    # Basic email validation
    if "@" not in test_email or "." not in test_email:
        print(f"❌ Invalid email address: {test_email}")
        sys.exit(1)

    # Run the async function
    asyncio.run(send_test_emails(test_email))


if __name__ == "__main__":
    main()
