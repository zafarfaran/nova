# Email Integrations - Automated Notifications

This document describes all the automated email notifications integrated throughout the Nova VAT system.

## Overview

The email system now automatically sends notifications for key events in the workflow, keeping clients informed and engaged throughout the VAT compliance process.

## 📧 Automated Email Scenarios

### 1. **Welcome Email** - When Client is Created

**Triggered by:** Creating a new client via chat or API

**Sent to:** Client's contact email

**Purpose:** Welcome new clients and provide onboarding link

**Email includes:**
- Welcome message personalized to the client
- Company name and VAT scheme information
- Onboarding link to complete their profile
- Next steps to get started

**Example:**
```
User in Chat: "Create a new client named Acme Ltd with email acme@example.com"
Nova: *Creates client and automatically sends welcome email*
Response: "Client 'Acme Ltd' created successfully. Welcome email sent to acme@example.com."
```

**API Usage:**
```bash
POST /api/v1/chat/stream
# When using create_client tool, email is sent automatically
```

---

### 2. **Validation Failure Email** - When Document Fails Validation

**Triggered by:** Document validation returning FAILED or WARNING status

**Sent to:** Client's contact email

**Purpose:** Notify client about validation issues that need fixing

**Email includes:**
- Document name and type
- List of validation issues with severity (❌ Failed, ⚠️ Warning)
- VAT period affected
- Clear call-to-action to re-upload corrected document

**Example:**
```
Scenario: Client uploads an invoice with incorrect VAT calculation
System: Validates document → Finds VAT calculation error
Action: Automatically sends email to client explaining the issue
```

**API Usage:**
```bash
POST /api/v1/validation/run/123
# After validation, if failures detected, email is sent automatically
```

**Email Content Example:**
```
Subject: Validation Issues Found in Invoice_2024.pdf

Dear John,

We found some issues with your uploaded document "Invoice_2024.pdf":

❌ VAT calculation mismatch: Net (£1000) + VAT (£200) ≠ Gross (£1150)
⚠️ Invoice date is outside VAT period Q4 2025

Please review and re-upload the corrected document.

Best regards,
Nova VAT Assistant
```

---

### 3. **Document Rejection Email** - When Accountant Rejects Document

**Triggered by:** Accountant explicitly rejecting a document via API

**Sent to:** Client's contact email

**Purpose:** Inform client why their document was rejected and what to do

**Email includes:**
- Document name being rejected
- Who rejected it (accountant name)
- Reason for rejection (detailed explanation)
- Instructions to upload corrected version

**API Usage:**
```bash
POST /api/v1/validation/reject/123
{
  "rejected_by": "Sarah Jones, Senior Accountant",
  "rejection_reason": "Invoice appears to be a duplicate of invoice #1234 from last month. Please verify and resubmit if this is a separate transaction."
}
```

**Response:**
```json
{
  "message": "Document rejected successfully",
  "document_id": 123,
  "email_sent": true,
  "rejected_by": "Sarah Jones, Senior Accountant"
}
```

---

### 4. **Missing Documents Email** - Via Chat Tool

**Triggered by:** Chat agent using send_email tool with missing_documents purpose

**Sent to:** Client's contact email

**Purpose:** Request missing documents needed for VAT return

**Example:**
```
User in Chat: "Send an email to Acme Ltd about their missing bank statements"
Nova: *Uses client lookup + send_email tool*
Email sent with:
  - List of missing documents
  - Due date
  - Upload instructions
```

**Chat Agent Usage:**
```
User: "Which clients need attention?"
Nova: "3 clients need attention:
       - Acme Ltd: Missing 2 documents
       - TechCo: 1 validation issue
       - BuildIt: 3 missing documents"

User: "Email Acme Ltd about their missing documents"
Nova: *Automatically composes and sends professional email*
```

---

### 5. **VAT Return Ready Email** - Manual/Automated

**Triggered by:** Calling the email notification service when VAT return is complete

**Sent to:** Client's contact email

**Purpose:** Notify client their VAT return is ready for review

**Email includes:**
- VAT period covered
- Period dates (start, end, due date)
- Link to review portal
- Call-to-action to approve

**API Usage:**
```python
from app.services.email import EmailNotificationService

email_service = EmailNotificationService(db=db)
await email_service.send_vat_return_ready_email(
    client_id=123,
    period_id=456
)
```

---

## 🛠️ Implementation Details

### EmailNotificationService

Located in: `app/services/email_notification_service.py`

**Available Methods:**

```python
# 1. Welcome email
await send_welcome_email(client_id, onboarding_link=None)

# 2. Validation failure
await send_validation_failure_email(document_id, validation_results)

# 3. Document rejection
await send_document_rejection_email(document_id, rejected_by, rejection_reason)

# 4. Missing documents
await send_missing_documents_email(client_id, missing_items, due_date=None)

# 5. VAT return ready
await send_vat_return_ready_email(client_id, period_id)
```

### Integration Points

**1. Chat Agent (app/ai/tools.py)**
- `_tool_create_client`: Sends welcome email automatically
- `_tool_send_email`: Allows manual email sending via chat

**2. Validation Service (app/services/validation_service.py)**
- `validate_document`: Sends email if validation fails/warns
- Uses background thread to avoid blocking

**3. Validation API (app/api/v1/validation.py)**
- `POST /validation/reject/{doc_id}`: Sends rejection email

**4. Chaser Service (app/services/chaser_service.py)**
- `send_chaser_email`: Sends missing documents email

---

## 📝 Email Templates (AI-Generated)

All email content is **dynamically generated by AI** based on:
- **Purpose**: Type of email (welcome, validation_issues, etc.)
- **Tone**: Professional, friendly, formal, or urgent
- **Context**: Client info, document details, validation results, etc.

The AI creates:
- ✅ Professional subject lines
- ✅ Personalized greeting
- ✅ Clear explanation of the issue/action
- ✅ Actionable next steps
- ✅ Professional closing

---

## 🔧 Configuration

All emails are sent via your configured SMTP server (IONOS):

```bash
# .env file
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USERNAME=accounts@yourdomain.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=accounts@yourdomain.com
SMTP_FROM_NAME=Nova VAT Assistant
SMTP_USE_TLS=true
```

---

## 📊 Email Flow Examples

### Complete Client Onboarding Flow

```
1. Accountant creates client via chat
   ↓
2. System sends welcome email with onboarding link
   ↓
3. Client uploads documents
   ↓
4. System validates documents
   ↓
5a. If validation fails → Email sent with issues
5b. If validation passes → Documents accepted
   ↓
6. If documents missing → Chat agent sends reminder
   ↓
7. All documents validated → VAT return ready email
```

### Document Rejection Flow

```
1. Client uploads invoice
   ↓
2. System extracts and validates
   ↓
3. Accountant reviews and rejects
   ↓
4. POST /api/v1/validation/reject/123
   ↓
5. System sends rejection email to client
   ↓
6. Client receives clear explanation
   ↓
7. Client uploads corrected document
```

---

## 🎯 Usage Examples

### Example 1: Create Client and Send Welcome
```python
# Via Chat
User: "Create client TechStartup Ltd with email tech@startup.com"

# System automatically:
# 1. Creates client
# 2. Creates VAT period
# 3. Creates checklist items
# 4. Sends welcome email with onboarding link
```

### Example 2: Validation Failure Notification
```python
# Document uploaded → Validation runs
validation_service.validate_document(doc_id=123)

# If failures found:
# → Email automatically sent to client
# → Email includes all validation issues
# → Client knows exactly what to fix
```

### Example 3: Accountant Rejects Document
```bash
curl -X POST "http://localhost:8000/api/v1/validation/reject/123" \
  -H "Content-Type: application/json" \
  -d '{
    "rejected_by": "Sarah Jones",
    "rejection_reason": "Duplicate invoice - already processed in last VAT period"
  }'

# Response:
{
  "message": "Document rejected successfully",
  "document_id": 123,
  "email_sent": true,
  "rejected_by": "Sarah Jones"
}
```

### Example 4: Send Missing Documents Email via Chat
```
User: "Email all clients who are missing documents"

Nova: "I found 3 clients with missing documents. Let me send emails..."
*Uses send_email tool for each client*
✓ Email sent to Acme Ltd about 2 missing items
✓ Email sent to BuildIt about 3 missing items
✓ Email sent to TechCo about 1 missing item
```

---

## 🚦 Error Handling

All email sending includes robust error handling:

- ✅ **Non-blocking**: Email failures don't break core functionality
- ✅ **Logged**: All attempts and failures are logged
- ✅ **Background**: Emails sent in background threads/tasks
- ✅ **Graceful degradation**: If email fails, system continues

**Example:**
```python
try:
    email_sent = await send_welcome_email(client_id)
except Exception as e:
    logger.error(f"Email failed: {e}")
    # Client still created successfully
    # Email failure doesn't rollback transaction
```

---

## 📈 Monitoring

Check logs for email activity:

```bash
# See all email notifications
grep "app.services.email.notification" logs/app.log

# See specific types
grep "Welcome email sent" logs/app.log
grep "Validation failure email" logs/app.log
grep "Rejection email sent" logs/app.log
```

**Log Examples:**
```
INFO | app.services.email.notification | Sending welcome email to client Acme Ltd (acme@example.com)
INFO | app.services.email.notification | Welcome email sent successfully to acme@example.com

INFO | app.services.email.notification | Sending validation failure email to john@example.com for document Invoice_2024.pdf
INFO | app.services.email.notification | Validation failure email sent successfully to john@example.com

INFO | app.services.email.notification | Sending rejection email to sarah@example.com for document Receipt_001.pdf
INFO | app.services.email.notification | Rejection email sent successfully to sarah@example.com
```

---

## 🔜 Future Enhancements

Potential additions:
- Email templates with custom branding
- Email delivery tracking (opens, clicks)
- Email scheduling/batching
- Client email preferences (opt-out certain types)
- SMS notifications for urgent items
- Webhook integrations
- Email queue with retry logic

---

## 🆘 Troubleshooting

### Emails not sending?

1. **Check SMTP config** in `.env`
2. **Check logs** for error messages
3. **Verify client has email** in database
4. **Test SMTP** with standalone email send
5. **Check spam folder** (client's inbox)

### Emails sending but content wrong?

1. **Check AI provider** is configured
2. **Review context_data** being passed
3. **Test email preview** endpoint
4. **Check AI generation** logs

---

## 📚 Related Files

- `app/services/email_service.py` - Core email sending
- `app/services/email_notification_service.py` - Automated notifications
- `app/ai/tools.py` - Chat agent email tool
- `app/services/validation_service.py` - Validation email integration
- `app/api/v1/validation.py` - Rejection endpoint
- `app/schemas/email.py` - Email request/response models

---

**Need help?** Check the main email agent guide in `EMAIL_AGENT_GUIDE.md` and IONOS setup in `IONOS_EMAIL_SETUP.md`.
