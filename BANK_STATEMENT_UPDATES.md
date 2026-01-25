# Bank Statement Updates

## Summary
Added two major features:
1. **Automatic checklist item creation** when bank transactions are fetched
2. **User choice UI** - Connect bank account OR upload statements manually

---

## Feature 1: Checklist Item on Transaction Fetch

### What Changed
When transactions are fetched via Plaid, a checklist item is automatically created/updated in the database.

### File Modified
`/src/app/api/plaid/fetch-transactions/route.ts`

### Checklist Item Details
- **Item ID**: `bank_statements` (for Plaid auto-fetch)
- **Title**: "Bank Statements (Auto-fetched from Plaid)"
- **Status**: `uploaded` (automatically marked as complete)
- **Acceptance**: `auto`
- **CTA Action**: `plaid_sync`
- **Uploaded File URL**: CSV file URL from UploadThing
- **CTA Data** (JSON):
  ```json
  {
    "transactionCount": 45,
    "startDate": "2025-10-27",
    "endDate": "2026-01-25",
    "fileName": "123_Banktransaction.csv",
    "fetchedAt": "2026-01-25T10:30:00.000Z"
  }
  ```

### Behavior
- If checklist item already exists → Updates it with new data
- If it doesn't exist → Creates a new one
- Tracks all transaction metadata for audit purposes

---

## Feature 2: User Choice UI - Connect or Upload

### What Changed
Users now see a choice screen asking if they want to:
1. **Connect Bank Account** (Recommended) - Automatic via Plaid
2. **Upload Manually** - Traditional file upload

### New Files Created

#### 1. `/src/app/onboard/[clientId]/BankStatementChoice.tsx`
**Purpose**: Shows the choice screen with two attractive options

**Features**:
- Beautiful card-based UI with icons
- Green card for "Connect Bank Account" (marked as recommended)
- Blue card for "Upload Manually"
- Shows benefits of each option
- "Back to options" button to change choice

#### 2. `/src/app/onboard/[clientId]/BankStatementChoiceWrapper.tsx`
**Purpose**: Manages state and handles the flow

**Features**:
- Shows choice screen initially
- When user picks "Connect Bank" → Shows BankConnectionButton
- When user picks "Manual Upload" → Creates checklist item and shows uploader
- Handles loading states
- Uses existing ChecklistUploader component

#### 3. `/src/app/api/checklist/create-bank-statement-item/route.ts`
**Purpose**: API endpoint to create manual upload checklist item

**Creates item with**:
- **Item ID**: `bank_statements_manual`
- **Title**: "Bank Statements (Manual Upload)"
- **Status**: `pending`
- **Acceptance**: `manual`
- **CTA Action**: `upload`

### File Modified
`/src/app/onboard/[clientId]/page.tsx`
- Replaced `<BankConnectionButton>` with `<BankStatementChoiceWrapper>`
- Updated section title from "Bank Account Connection" to "Bank Statements"

---

## User Flow

### Scenario 1: Connect Bank Account (Automatic)
1. User sees choice screen
2. Clicks "Connect Bank Account" (green card)
3. Plaid Link opens
4. User connects bank → Transactions auto-fetch
5. **Checklist item created automatically** with:
   - Item ID: `bank_statements`
   - Status: `uploaded`
   - File URL: CSV in UploadThing

### Scenario 2: Manual Upload
1. User sees choice screen
2. Clicks "Upload Manually" (blue card)
3. API creates checklist item with ID: `bank_statements_manual`
4. Shows file upload interface
5. User uploads PDF/CSV/Excel files
6. Files saved via UploadThing
7. **Checklist item marked as uploaded**

---

## Benefits

### For Users
✅ **Choice & Control** - Pick what works for them
✅ **Clear options** - Beautiful UI explains each method
✅ **Flexibility** - Can switch between methods
✅ **Security notice** - "Your data is encrypted and secure"

### For Accountants
✅ **Automatic tracking** - All bank statements logged in checklist
✅ **Audit trail** - Know exactly how statements were provided
✅ **Metadata storage** - Transaction count, date ranges, etc.
✅ **Unified interface** - Manual and auto both show in checklist

---

## Database Schema

### ChecklistItem Fields Used

| Field | Plaid Auto | Manual Upload |
|-------|-----------|---------------|
| `itemId` | `bank_statements` | `bank_statements_manual` |
| `title` | "Bank Statements (Auto-fetched from Plaid)" | "Bank Statements (Manual Upload)" |
| `status` | `uploaded` | `pending` → `uploaded` |
| `acceptance` | `auto` | `manual` |
| `ctaAction` | `plaid_sync` | `upload` |
| `ctaData` | JSON with transaction metadata | JSON with upload metadata |
| `uploadedFileUrl` | CSV file URL | Uploaded file URL(s) |

---

## UI Components

### Choice Screen Features
- **Responsive grid** - 2 columns on desktop, stacks on mobile
- **Icons** - Lightning bolt for auto, cloud upload for manual
- **Checkmarks** - Shows benefits of each option
- **Hover effects** - Cards highlight on hover
- **Security badge** - Lock icon with encryption message

### Manual Upload Features
- **Drag & drop zone** (via ChecklistUploader)
- **Multi-file support** - Upload multiple statements at once
- **File type validation** - PDF, CSV, Excel only
- **Progress indicator** - Shows upload status
- **Success confirmation** - Alert when complete

---

## Testing

### Test Plaid Auto-Fetch
1. Go to onboarding page
2. Choose "Connect Bank Account"
3. Connect with Plaid (use `user_good` / `pass_good` in sandbox)
4. Check database - `bank_statements` checklist item should exist
5. Verify CSV file uploaded to UploadThing

### Test Manual Upload
1. Go to onboarding page
2. Choose "Upload Manually"
3. Upload a PDF/CSV file
4. Check database - `bank_statements_manual` checklist item should exist
5. Verify file uploaded to UploadThing

---

## Files Summary

### New Files (3)
1. `src/app/onboard/[clientId]/BankStatementChoice.tsx` - Choice UI
2. `src/app/onboard/[clientId]/BankStatementChoiceWrapper.tsx` - State management
3. `src/app/api/checklist/create-bank-statement-item/route.ts` - API endpoint

### Modified Files (2)
1. `src/app/api/plaid/fetch-transactions/route.ts` - Added checklist item creation
2. `src/app/onboard/[clientId]/page.tsx` - Replaced BankConnectionButton with choice wrapper

---

## What's Next

Accountants can now:
- ✅ See bank statements in the checklist (both auto and manual)
- ✅ Know how statements were provided (auto vs manual)
- ✅ Access transaction metadata (count, date range, etc.)
- ✅ Download CSV files from UploadThing
- ✅ Track completion status for each client

Clients get:
- ✅ Clear choice between auto and manual
- ✅ Beautiful, intuitive UI
- ✅ Flexibility to change their mind
- ✅ Confidence with security messaging
