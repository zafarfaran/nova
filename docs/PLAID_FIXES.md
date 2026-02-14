# Plaid Integration Fixes

## Summary
Fixed the "no eligible accounts" error and added automatic transaction fetching with UploadThing storage.

## Changes Made

### 1. Fixed "No Eligible Accounts" Error
**File:** `/src/app/api/plaid/create-link-token/route.ts`

**Changes:**
- Changed from `Products.Auth, Products.Transactions` to just `Products.Transactions`
- Added `account_filters` to specifically request checking and savings accounts
- This fixes the issue where Plaid Link couldn't find eligible accounts

**Why this fixes it:**
- Requesting both Auth and Transactions can cause conflicts in some Plaid environments
- Adding explicit account filters ensures only valid depository accounts are shown
- Checking and savings accounts are the most common account types that support transactions

### 2. Created Transaction Fetching Endpoint
**File:** `/src/app/api/plaid/fetch-transactions/route.ts` (NEW)

**Features:**
- Fetches transactions from ALL connected bank accounts for a client
- Gets last 90 days of transactions
- Converts to CSV format with proper headers
- Uploads to UploadThing with filename: `{clientId}_Banktransaction.csv`
- Returns transaction count and file URL

**CSV Format:**
```
Account Name,Institution,Date,Description,Amount,Currency,Category,Status,Transaction ID,Merchant
```

### 3. Automatic Transaction Fetching After Connection
**File:** `/src/app/api/plaid/exchange-token/route.ts`

**Changes:**
- After successfully connecting bank accounts, automatically triggers transaction fetch in background
- Non-blocking - doesn't delay the response to the user
- Client gets their accounts connected immediately, transactions are fetched asynchronously

### 4. Added Manual Transaction Fetch Button
**File:** `/src/app/onboard/[clientId]/BankConnectionButton.tsx`

**Changes:**
- Added "Fetch Bank Transactions" button (green, appears only when accounts are connected)
- Shows loading state while fetching
- Displays success message with transaction count and filename
- Allows users to refresh transactions manually anytime

## How It Works

### Connection Flow:
1. User clicks "Connect Bank Account"
2. Plaid Link opens with proper filters
3. User selects checking/savings accounts
4. Accounts are saved to database
5. **Transactions are automatically fetched in background**
6. User sees success message

### Transaction Fetch:
1. Queries all active bank connections for the client
2. For each connection, calls Plaid `transactionsGet()` API
3. Fetches last 90 days of transactions
4. Combines all transactions from all accounts
5. Converts to CSV with proper escaping
6. Uploads to UploadThing with naming format: `{clientId}_Banktransaction.csv`
7. Returns file URL and transaction count

## Environment Variables Required

Make sure these are set in `.env`:
```bash
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox  # or development/production
UPLOADTHING_TOKEN=your_uploadthing_token
NEXTAUTH_URL=http://localhost:3000
```

## Testing in Sandbox

For Plaid Sandbox testing, use these test credentials:
- **Institution:** Any bank (e.g., search "Chase")
- **Username:** `user_good`
- **Password:** `pass_good`
- **MFA:** `1234`

This will connect successfully and allow transaction fetching.

## Files Changed

1. ✅ `/src/app/api/plaid/create-link-token/route.ts` - Fixed account filters
2. ✅ `/src/app/api/plaid/fetch-transactions/route.ts` - NEW - Transaction fetching
3. ✅ `/src/app/api/plaid/exchange-token/route.ts` - Auto-fetch trigger
4. ✅ `/src/app/onboard/[clientId]/BankConnectionButton.tsx` - Manual fetch button

## API Endpoints

### POST `/api/plaid/fetch-transactions`
**Request:**
```json
{
  "clientId": 123
}
```

**Response:**
```json
{
  "success": true,
  "count": 45,
  "fileUrl": "https://uploadthing.com/f/abc123.csv",
  "fileName": "123_Banktransaction.csv",
  "startDate": "2025-10-27",
  "endDate": "2026-01-25"
}
```

## Transaction Data Saved

Each transaction CSV includes:
- Account Name
- Institution Name
- Transaction Date
- Description
- Amount (positive for credits, negative for debits)
- Currency (GBP/USD)
- Category
- Status (Pending/Posted)
- Transaction ID (unique identifier)
- Merchant Name

## Notes

- ✅ Transactions are fetched automatically after bank connection
- ✅ Users can manually refresh transactions anytime
- ✅ File naming: `{clientId}_Banktransaction.csv`
- ✅ Files stored in UploadThing for easy access
- ⚠️ Access tokens stored in plaintext (consider encrypting in production)
- ⚠️ 90-day transaction window (adjustable in code)
- ⚠️ 500 transaction limit per account (increase with pagination if needed)
