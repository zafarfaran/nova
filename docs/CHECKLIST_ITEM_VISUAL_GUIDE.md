# Checklist Item / Request Item - Visual Guide

## 🎯 Simple Explanation

A **RequestItem** (displayed as "ChecklistItem" in the UI) is **one item on a document checklist** that a client needs to complete.

Think of it like a shopping list item:
- ☐ "Buy milk" (RequestItem with status: `pending`)
- ✅ "Buy bread" (RequestItem with status: `complete`)

## 📊 Real-World Example

### Scenario: Client "Acme Corp" needs to submit Q1 2024 VAT Return

```
Client: Acme Corp Ltd
  └── Engagement: Q1 2024 VAT Return (Jan-Mar 2024)
      └── RequestSet: "Q1 2024 Document Checklist"
          ├── RequestItem #1: "Upload VAT Certificate" (required, pending)
          ├── RequestItem #2: "Upload Bank Statements" (required, received)
          ├── RequestItem #3: "Upload Invoices" (optional, complete)
          └── RequestItem #4: "Upload Receipts" (optional, pending)
```

## 🔄 Complete Integration Flow

### Step 1: Backend Creates RequestItems

```python
# When accountant sets up client engagement
engagement = Engagement.create(client_id=1, period_start="2024-01-01", period_end="2024-03-31")
request_set = RequestSet.create(engagement_id=engagement.id, name="Q1 2024 Documents")

# Create request items from template
request_item = RequestItem.create(
    request_set_id=request_set.id,
    document_type_id=5,  # VAT Certificate
    description="Upload your VAT registration certificate",
    is_required=True,
    status="pending"
)
```

### Step 2: Frontend Fetches and Displays

```typescript
// Server component fetches data
const requestSets = await listRequestSets(engagementId);
const requestItems = await listRequestItems(requestSetId);

// Client component displays
<OnboardingContent 
    client={{
        requestItems: [
            {
                id: 1,
                description: "Upload your VAT registration certificate",
                is_required: true,
                status: "pending"
            },
            // ... more items
        ]
    }}
/>
```

### Step 3: User Sees Checklist

```
┌─────────────────────────────────────────┐
│ Required Documents                      │
├─────────────────────────────────────────┤
│ ☐ Upload your VAT registration          │
│   certificate                    [REQUIRED] │
│                                         │
│ ☑ Upload Bank Statements                │
│   (Uploaded)                     [REQUIRED] │
└─────────────────────────────────────────┘
```

### Step 4: User Uploads Document

```typescript
// User clicks "Upload" button
<UploadButton
    onClientUploadComplete={async (file) => {
        // 1. Update RequestItem status
        await updateRequestItem(itemId, { status: "received" });
        
        // 2. Sync document to backend
        await syncDocumentToBackend(clientId, itemId, file);
    }}
/>
```

### Step 5: Backend Links Document

```python
# Backend receives sync request
document = Document.create(
    filename="vat_certificate.pdf",
    external_url="https://uploadthing.com/...",
    client_id=1
)

# Link document to request item
request_item.documents.append(document)

# Auto-update status if enough documents uploaded
if len(request_item.documents) >= request_item.expected_count:
    request_item.status = "received"  # or "complete" if reviewed
```

### Step 6: Frontend Updates UI

```
┌─────────────────────────────────────────┐
│ Required Documents                      │
├─────────────────────────────────────────┤
│ ☑ Upload your VAT registration          │
│   certificate (Uploaded)         [REQUIRED] │
│                                         │
│ ☑ Upload Bank Statements                │
│   (Uploaded)                     [REQUIRED] │
└─────────────────────────────────────────┘
Progress: 2/2 (100%)
```

## 🗂️ Data Structure

### Backend Database

```sql
-- request_items table
id | request_set_id | document_type_id | description | is_required | status
1  | 1              | 5                | "Upload VAT certificate" | true | "pending"
2  | 1              | 3                | "Upload Bank Statements" | true | "received"

-- request_item_documents (junction table)
request_item_id | document_id
2              | 10  -- Bank statement PDF linked to RequestItem #2
```

### Frontend State

```typescript
const requestItems: RequestItem[] = [
    {
        id: 1,
        request_set_id: 1,
        document_type_id: 5,
        description: "Upload your VAT registration certificate",
        is_required: true,
        status: "pending",
        expected_count: 1,
        // ... other fields
    },
    {
        id: 2,
        request_set_id: 1,
        document_type_id: 3,
        description: "Upload Bank Statements",
        is_required: true,
        status: "received",  // Document uploaded!
        expected_count: 1,
    }
];
```

## 🔗 API Integration Points

### 1. Fetching RequestItems

```typescript
// Get all request items for a request set
import { listRequestItems } from "~/domains/requests/api/request";

const response = await listRequestItems(requestSetId);
// Returns: { items: RequestItem[], total: number }
```

### 2. Updating Status

```typescript
// When user uploads document
import { updateRequestItem } from "~/domains/requests/api/request";

await updateRequestItem(itemId, {
    status: "received"  // Document uploaded
});
```

### 3. Linking Documents

```typescript
// When document is uploaded via UploadThing
await fetch("/api/sync-document", {
    method: "POST",
    body: JSON.stringify({
        clientId: 1,
        checklistItemId: itemId,  // This is the RequestItem ID
        fileUrl: "https://uploadthing.com/...",
        documentType: "vat_certificate"
    })
});

// Backend automatically:
// 1. Creates Document record
// 2. Links it to RequestItem via request_item_documents table
// 3. Updates RequestItem status if needed
```

## 🎨 Component Hierarchy

```
OnboardingPage (Server Component)
  └── Fetches: Client, Engagement, RequestSets, RequestItems
      └── OnboardingContent (Client Component)
          └── ChecklistSection
              └── ChecklistItem (displays RequestItem)
                  ├── Shows: description, status, is_required
                  ├── UploadButton (when pending)
                  └── Status badge (pending/received/complete/waived)
```

## 💡 Key Takeaways

1. **RequestItem** = One document request in the checklist
2. **RequestSet** = Group of related RequestItems (e.g., "Q1 2024 Documents")
3. **Engagement** = Tax period/work assignment (e.g., "Q1 2024 VAT Return")
4. **Document** = Uploaded file that gets linked to RequestItem
5. **Status Flow**: `pending` → `received` → `complete` (or `waived`)

## 🔍 Why "ChecklistItem" Name?

The frontend component is called `ChecklistItem.tsx` for historical reasons (it used to work with Prisma ChecklistItem), but:
- ✅ It now works with `RequestItem` data from backend
- ✅ All API calls use `/api/v1/requests/items` endpoints
- ✅ Types are `RequestItem`, not `ChecklistItem`

**The name is just legacy - the functionality is RequestItem-based!**
