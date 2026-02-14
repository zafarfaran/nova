# Checklist Item - Simple Explanation

## 🎯 What is it?

A **Checklist Item** (backend calls it **RequestItem**) is **one thing a client needs to upload** during onboarding.

**Think of it like a to-do list:**
- ☐ Upload VAT certificate
- ☐ Upload bank statements  
- ☐ Upload invoices

Each of these is a **RequestItem**.

## 📊 The Hierarchy

```
Client (Acme Corp)
  └── Engagement (Q1 2024 VAT Return)
      └── RequestSet (Q1 2024 Document Checklist)
          ├── RequestItem #1: "Upload VAT Certificate" (required)
          ├── RequestItem #2: "Upload Bank Statements" (required)
          └── RequestItem #3: "Upload Invoices" (optional)
```

## 🔄 How It Works

### 1. **Backend Creates RequestItem**
When an accountant sets up a client, the backend creates RequestItems from a template:
```python
RequestItem(
    description="Upload your VAT registration certificate",
    is_required=True,
    status="pending"
)
```

### 2. **Frontend Displays It**
The frontend shows it as a checklist item:
```
┌─────────────────────────────────────┐
│ ☐ Upload your VAT registration      │
│   certificate                [REQUIRED] │
└─────────────────────────────────────┘
```

### 3. **User Uploads Document**
When the client uploads a file, it gets linked to the RequestItem:
- Document uploaded → Linked to RequestItem
- Backend auto-updates status: `pending` → `partial` → `complete`

### 4. **Status Updates**
- **pending**: No documents yet
- **partial**: Some documents uploaded (but not all if expected_count > 1)
- **complete**: All expected documents uploaded
- **waived**: Not applicable

## 🔌 Backend ↔ Frontend Integration

### Backend Model
```python
# backend/app/models/requests/item.py
class RequestItem:
    id: int
    request_set_id: int
    description: str  # "Upload your VAT certificate"
    is_required: bool
    status: "pending" | "partial" | "complete" | "waived"
    expected_count: int  # How many documents needed
    documents: List[Document]  # Uploaded files
```

### Frontend Type
```typescript
// src/domains/requests/types/index.ts
interface RequestItem {
    id: number;
    request_set_id: number;
    description: string | null;
    is_required: boolean;
    status: "pending" | "partial" | "complete" | "waived";
    expected_count: number;
    // ... other fields
}
```

### API Flow
```
Frontend                    Backend
   │                           │
   ├─ GET /api/v1/requests/   │
   │  items?request_set_id=1   │
   │──────────────────────────>│
   │                           ├─ Query RequestItems
   │                           ├─ Join with Documents
   │<──────────────────────────┤
   │  { items: RequestItem[] } │
   │                           │
   ├─ User uploads file       │
   │──────────────────────────>│
   │  POST /api/sync-document  │
   │                           ├─ Create Document
   │                           ├─ Link to RequestItem
   │                           ├─ Auto-update status
   │<──────────────────────────┤
   │  { success: true }        │
   │                           │
   ├─ PATCH /api/v1/requests/  │
   │  items/{id}                │
   │  { status: "complete" }    │
   │──────────────────────────>│
   │                           ├─ Update RequestItem
   │<──────────────────────────┤
   │  { id: 1, status: "complete" } │
```

## 🎨 Frontend Component

The component `ChecklistItem.tsx` displays a RequestItem:

```typescript
<ChecklistItem 
    item={requestItem}  // RequestItem from backend
    clientId={123}
    onItemUpdate={(id, payload) => {
        // Updates RequestItem via API
        updateRequestItem(id, { status: "complete" });
    }}
/>
```

**Note**: Despite the name "ChecklistItem", it works with `RequestItem` data!

## 📝 Key Fields Explained

| Field | Meaning | Example |
|-------|---------|---------|
| `description` | What the client needs to do | "Upload your VAT certificate" |
| `is_required` | Must be completed? | `true` = required, `false` = optional |
| `status` | Current state | `pending`, `partial`, `complete`, `waived` |
| `expected_count` | How many documents needed | Usually `1`, can be more |
| `document_type_id` | Type of document | Links to DocumentType (invoice, receipt, etc.) |

## 🔄 Status Flow

```
pending  →  partial  →  complete
   ↓
waived
```

- **pending**: No documents uploaded
- **partial**: Some documents uploaded (if expected_count > 1, or waiting for review)
- **complete**: All documents uploaded and reviewed
- **waived**: Not applicable for this client

## 💡 Why the Confusion?

The frontend component is called `ChecklistItem.tsx` (old name), but:
- ✅ It displays `RequestItem` data from backend
- ✅ All API calls use `/api/v1/requests/items` endpoints
- ✅ Types are `RequestItem`, not `ChecklistItem`

**It's just a naming legacy - the functionality is RequestItem-based!**

## 🎓 Summary

**RequestItem** = One document request in the onboarding checklist
- Belongs to a RequestSet (group of requests)
- Has a status that tracks completion
- Can be required or optional
- Links to uploaded Documents
- Displayed in UI as a checklist item

**Simple analogy**: It's like one item on a shopping list that you check off when done!
