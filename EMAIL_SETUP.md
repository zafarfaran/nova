# Email Functionality Setup Guide

## Overview
Nova can send AI-generated, branded emails to clients directly from the dashboard. The "Send Reminder" feature uses Claude AI to generate personalized email content with Nova branding.

## Features
- **AI-Generated Content**: Claude generates contextual emails based on client data
- **Nova Branding**: All emails include the Nova logo and professional HTML templates
- **Multiple Email Types**: Reminders, validation issues, welcome emails, VAT return notifications, etc.
- **Real-time Status**: Loading states and success/error feedback

## Backend Setup (Required)

### 1. Configure SMTP Settings
Add these environment variables to `/backend/.env`:

```bash
# SMTP Configuration (Required for sending emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=noreply@nova.app
SMTP_FROM_NAME=Nova

# Application URL (for email links)
APP_URL=http://localhost:3000
```

### 2. Gmail Setup (If using Gmail)
1. Go to Google Account Settings → Security
2. Enable 2-Factor Authentication
3. Generate an App Password for "Mail"
4. Use the app password as `SMTP_PASSWORD`

### 3. AI Provider Setup
Ensure you have AI provider configured:

```bash
# AI Configuration
ANTHROPIC_API_KEY=your-claude-api-key
# OR
OPENAI_API_KEY=your-openai-api-key

AI_PROVIDER=anthropic  # or "openai"
```

## Frontend Setup

Add to `/src/app/.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing Email Functionality

### 1. Start the Backend
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend
```bash
npm run dev
# Runs on http://localhost:3000
```

### 3. Send a Test Email from Dashboard
1. Navigate to `/accountant` in your browser
2. Click on any client to open the detail panel
3. Click the "Send Reminder" button
4. Check the client's email inbox for the AI-generated reminder

### 4. Test All Email Types (Optional)
Run the comprehensive email test script:

```bash
cd backend
python test_emails.py your-email@example.com
```

This sends all 9 email types:
- Welcome Email
- Validation Issues
- Document Rejection
- Missing Documents
- VAT Return Ready
- Reminder
- Invoice Request
- Follow-up
- General Communication

## Email API Endpoints

### Send Email
**POST** `/api/v1/email/send`

Request body:
```json
{
  "to_email": "client@example.com",
  "to_name": "John Smith",
  "purpose": "reminder",
  "tone": "friendly",
  "client_id": 123,
  "context_data": {
    "reminder_type": "document upload reminder",
    "documents_missing": 3,
    "vat_period": "Q1 2026",
    "due_date": "7 February 2026"
  }
}
```

Response:
```json
{
  "success": true,
  "message": "Email sent successfully",
  "message_id": "<...>",
  "generated_subject": "Reminder: Upload Your Documents for Q1 2026",
  "generated_body": "...",
  "sent_at": "2026-01-25T12:34:56Z"
}
```

### Preview Email (Without Sending)
**POST** `/api/v1/email/preview`

Query parameters:
- `purpose`: Email purpose (e.g., "reminder")
- `tone`: Email tone (e.g., "friendly")
- `client_id`: Client ID (optional)
- `context_data`: Additional context (optional)

## Email Purposes

Available email purposes:
- `reminder` - General reminders
- `missing_documents` - Request missing documents
- `vat_return_ready` - Notify VAT return is ready
- `validation_issues` - Inform about document validation issues
- `welcome` - Welcome new clients
- `invoice_request` - Request specific invoices
- `follow_up` - Follow up on previous communications
- `general` - General communications

## Email Tones

Available tones:
- `formal` - Very professional and formal
- `professional` - Professional but approachable
- `friendly` - Warm and conversational
- `urgent` - Urgent but professional

## Troubleshooting

### SMTP Authentication Failed
- Check your SMTP credentials are correct
- For Gmail, ensure you're using an App Password, not your regular password
- Verify 2FA is enabled on your Google account

### Emails Not Received
- Check spam/junk folder
- Verify the client email address is correct
- Check backend logs for delivery errors
- Test with a different email provider

### Backend Not Connected
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in frontend .env
- Verify CORS is configured correctly in backend

### AI Generation Failed
- Verify AI provider API key is valid
- Check you have API credits/quota remaining
- Review backend logs for specific errors

## Next.js API Route

The frontend uses a Next.js API route at `/api/email/send-reminder` that proxies to the backend FastAPI service. This route:
1. Validates client data
2. Prepares context for AI generation
3. Calls the backend `/api/v1/email/send` endpoint
4. Returns success/error to the frontend

Location: `/src/app/api/email/send-reminder/route.ts`

## Email Template

All emails use a professional HTML template with:
- Nova logo in the header
- Clean, readable typography
- Off-white backgrounds (#fafafa)
- Simple borders (#e8e8e8)
- Responsive design
- Branded footer: "Powered by Nova - 10x Your Accounting Power"

Template location: `/backend/app/services/email_service.py` → `_wrap_in_html_template()`

## Related Files

**Backend:**
- `/backend/app/api/v1/email.py` - Email API endpoints
- `/backend/app/services/email_service.py` - Email composition and sending
- `/backend/app/services/email_notification_service.py` - Automated notifications
- `/backend/app/schemas/email.py` - Email request/response schemas
- `/backend/test_emails.py` - Email testing script

**Frontend:**
- `/src/app/api/email/send-reminder/route.ts` - Next.js API route
- `/src/app/accountant/DashboardClient.tsx` - Dashboard with send reminder logic
- `/src/app/accountant/components/DetailPanel.tsx` - Client detail panel with button

## Support

For issues or questions about the email functionality:
1. Check the backend logs: `uvicorn app.main:app --reload`
2. Check the browser console for frontend errors
3. Review the API documentation: `http://localhost:8000/docs`
4. Test with the email test script: `python test_emails.py`
