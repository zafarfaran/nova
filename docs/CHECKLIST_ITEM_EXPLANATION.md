# Checklist Item / Request Item Explanation

## 🎯 What is a "Checklist Item"?

A **Checklist Item** (now called **Request Item** in the backend) is a **single document request** that needs to be completed by a client during onboarding.

Think of it like a to-do list item:
- ✅ "Upload your VAT certificate"
- ✅ "Provide bank statements for Q1 2024"
- ✅ "Submit invoices for the tax period"

## 📊 The Evolution: ChecklistItem → RequestItem

### Old System (Prisma - Removed)
- **Model**: `ChecklistItem`
- **Purpose**: Simple checklist tracking
- **Fields**: `title`, `status`, `required`, `acceptance`
- **Status**: ❌ **REMOVED** - No longer used

### New System (Backend - Current)
- **Model**: `RequestItem` (in `backend/app/models/requests/item.py`)
- **Purpose**: Structured document request system
- **Fields**: `description`, `status`, `is_required`, `document_type_id`, `expected_count`
- **Status**: ✅ **ACTIVE** - This is what we use now

## 🏗️ Architecture Overview

```
Client
  └── Engagement (VAT Period)
      └── RequestSet (Group of requests, e.g., "Q1 2024 VAT Return")
          └── RequestItem (Individual document request)
              └── Documents (Uploaded files linked to this request)
```

### Example Flow:

1. **Client Created**: "Acme Corp Ltd"
2. **Engagement Created**: VAT Return for Q1 2024 (Jan-Mar 2024)
3. **RequestSet Created**: "Q1 2024 Document Requests"
4. **RequestItems Created** (from template):
   - "Upload VAT Certificate" (required)
   - "Upload Bank Statements" (required)
   - "Upload Invoices" (optional)
5. **Client Uploads Documents**: Each document gets linked to a RequestItem
6. **Status Updates**: RequestItem status changes: `pending` → `received` → `complete`

## 📋 RequestItem Structure

### Backend Model (`backend/app/models/requests/item.py`)

```python
class RequestItem:
    id: int
    request_set_id: int              # Which RequestSet this belongs to
    document_type_id: int             # What type of document (invoice, receipt, etc.)
    description: str                  # "Upload your VAT certificate"
    expected_count: int = 1           # How many documents expected
    is_required: bool = True          # Must be completed?
    status: RequestItemStatus         # pending | received | complete | waived
    due_date: date | None            # When it's due
    assigned_to_contact_id: int | None
    documents: List[Document]          # Uploaded files linked to this item
```

### Frontend Type (`src/domains/requests/types/index.ts`)

```typescript
interface RequestItem {
    id: number;
    request_set_id: number;
    document_type_id: number | null;
    description: string | null;        // "Upload your VAT certificate"
    expected_count: number;            // Usually 1
    is_required: boolean;               // true = required, false = optional
    status: RequestItemStatus;         // "pending" | "received" | "complete" | "waived"
    due_date: string | null;           // ISO date string
    assigned_to_contact_id: number | null;
    created_at: string;
    updated_at: string;
}
```

## 🔄 Status Flow

```
pending  →  received  →  complete
   ↓
waived
```

- **`pending`**: Not started yet
- **`received`**: Document uploaded (but not reviewed)
- **`complete`**: Document uploaded and reviewed/approved
- **`waived`**: Not applicable for this client

## 🔌 Backend Integration

### API Endpoints

```typescript
// List request items for a request set
GET /api/v1/requests/items?request_set_id=123

// Get a single request item
GET /api/v1/requests/items/{id}

// Update request item status
PATCH /api/v1/requests/items/{id}
{
  "status": "received"  // or "complete", "waived"
}

// Link a document to a request item
POST /api/v1/requests/items/{id}/documents/{document_id}
```

### How Documents Link to RequestItems

1. Client uploads a document via UploadThing
2. Frontend calls `/api/sync-document` with `checklistItemId` (which is actually `requestItemId`)
3. Backend creates a `Document` record
4. Backend links document to `RequestItem` via `request_item_documents` junction table
5. `RequestItem.status` automatically updates based on document count

## 🎨 Frontend Integration

### Component: `ChecklistItem.tsx`

**Note**: Despite the name "ChecklistItem", this component actually works with `RequestItem` data!

```typescript
// Component receives RequestItem from backend
<ChecklistItem 
    item={requestItem}  // RequestItem type
    clientId={123}
    onItemUpdate={(id, payload) => {
        // Updates RequestItem status via API
        updateRequestItem(id, { status: "received" });
    }}
/>
```

### Data Flow

```
1. Server Component (page.tsx)
   ↓ Fetches from backend
   listRequestSets(engagementId)
   ↓
   listRequestItems(requestSetId)
   ↓
   Returns RequestItem[]

2. Client Component (OnboardingContent.tsx)
   ↓ Receives RequestItem[]
   Maps to ChecklistItem components
   ↓
   <ChecklistItem item={requestItem} />

3. User Uploads Document
   ↓
   UploadButton → UploadThing
   ↓
   syncDocumentToBackend()
   ↓
   Backend links Document to RequestItem
   ↓
   updateRequestItem(id, { status: "received" })
```

## 📝 Example: Complete Flow

### 1. Backend Creates RequestItem

```python
# When creating from template
request_item = RequestItem(
    request_set_id=1,
    document_type_id=5,  # "VAT Certificate"
    description="Upload your VAT registration certificate",
    is_required=True,
    status=RequestItemStatus.PENDING,
    expected_count=1
)
```

### 2. Frontend Displays It

```typescript
// In OnboardingContent.tsx
const requestItems = await listRequestItems(requestSetId);

// Renders as:
<ChecklistItem 
    item={{
        id: 1,
        description: "Upload your VAT registration certificate",
        is_required: true,
        status: "pending"
    }}
/>
```

### 3. User Uploads Document

```typescript
// User clicks upload button
<UploadButton
    onClientUploadComplete={async (res) => {
        // 1. Update status to "received"
        await updateRequestItem(item.id, { status: "received" });
        
        // 2. Sync document to backend
        await syncDocumentToBackend(clientId, item.id, file, "vat_certificate");
    }}
/>
```

### 4. Backend Links Document

```python
# Backend receives sync request
document = Document.create(...)
request_item.documents.append(document)

# Status auto-updates if expected_count met
if len(request_item.documents) >= request_item.expected_count:
    request_item.status = RequestItemStatus.RECEIVED
```

## 🎯 Key Concepts

### RequestItem vs ChecklistItem

| Aspect | Old (ChecklistItem) | New (RequestItem) |
|--------|---------------------|-------------------|
| **Model** | Prisma `ChecklistItem` | Backend `RequestItem` |
| **Purpose** | Simple checklist | Document request system |
| **Document Link** | Single file URL | Many-to-many with Documents |
| **Type System** | String-based | DocumentType ID |
| **Status** | `uploaded`, `confirmed` | `pending`, `received`, `complete`, `waived` |
| **Status** | ❌ Removed | ✅ Active |

### Why the Confusion?

The frontend component is still called `ChecklistItem.tsx` for historical reasons, but:
- ✅ It works with `RequestItem` data from backend
- ✅ All API calls use RequestItem endpoints
- ✅ Types are `RequestItem`, not `ChecklistItem`

**Recommendation**: Consider renaming `ChecklistItem.tsx` → `RequestItem.tsx` for clarity.

## 🔍 Where RequestItems Come From

### 1. Templates
- RequestTemplates define standard document requests
- When creating an Engagement, a RequestSet is created from a template
- Template items become RequestItems

### 2. Manual Creation
- Accountant can manually create RequestItems via API
- `POST /api/v1/requests/items`

### 3. Programmatic
- Created when setting up a new client engagement
- Based on client type (sole_trader vs limited_company)

## 📚 Related Concepts

- **RequestSet**: A group of RequestItems (e.g., "Q1 2024 VAT Return Documents")
- **Engagement**: A tax period/work assignment (e.g., "Q1 2024 VAT Return")
- **Document**: An uploaded file that can be linked to multiple RequestItems
- **DocumentType**: Categorization (invoice, receipt, bank_statement, etc.)

## 🎓 Summary

**RequestItem** = A single document request in the onboarding checklist
- Belongs to a RequestSet
- Has a status (pending → received → complete)
- Can be required or optional
- Links to uploaded Documents
- Displayed in frontend as a "ChecklistItem" component

The terminology is confusing because the frontend still uses "checklist" language, but the backend uses "request" terminology. They're the same thing - just different naming conventions!
