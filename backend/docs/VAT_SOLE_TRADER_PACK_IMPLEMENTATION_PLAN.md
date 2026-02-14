# VAT Sole Trader Pack — Implementation Plan

## Overview

Implement the VAT Sole Trader Pack system following the canonical workflow:
- **Request → Upload**: Request Set template → Client uploads through portal
- **Classify → Extract → Validate**: AI processes documents
- **Review → Approve**: Accountant reviews and approves documents
- **Pack Builder → Export**: Build pack from approved documents

---

## Phase 1: Database & Data Layer

### 1.1 Document Types Setup
**Status**: ✅ Started (seed script created)

**Tasks**:
- [x] Create seed script for VAT ST document types
- [ ] Run seed script to populate database
- [ ] Verify all document types exist:
  - Core types (6): Bank statements, Sales evidence (3 variants), Credit notes, Purchase invoices, Purchase credit notes, Expense receipts
  - Optional types (10): Processor reports, Cash log, Card statements, VAT scheme docs, etc.

**Files**:
- `backend/app/scripts/seed_vat_sole_trader_pack.py`

**Notes**:
- Handle "choose one" for sales evidence (invoices OR POS summary OR cashbook)
- All document types should have `client_type_scope="sole_trader"`

---

### 1.2 Request Template Setup
**Status**: ✅ Started

**Tasks**:
- [x] Create RequestTemplate: "VAT Sole Trader Pack (UK)"
  - `client_type="sole_trader"`
  - `engagement_type="vat_return"`
- [x] Create RequestTemplateItems with:
  - Proper `order_index` (1-16)
  - Descriptions with `[Q_START]` and `[Q_END]` placeholders
  - `is_required` flags (core=required, optional=not required)
  - Handle "choose one" group for sales evidence

**Files**:
- `backend/app/scripts/seed_vat_sole_trader_pack.py`

**Special Handling**:
- Sales evidence "choose one": Create 3 separate template items, all marked `is_required=False` (at least one should be provided, but not all)

---

## Phase 2: Service Layer

### 2.1 Template-to-RequestSet Service
**Status**: ⏳ Pending

**Tasks**:
- [ ] Add `create_from_template()` method to `RequestSetService`
  - Input: `engagement_id`, `template_id`, optional `name_override`
  - Process:
    1. Get template and engagement
    2. Validate engagement type matches template
    3. Create RequestSet with period-based name: `"VAT Sole Trader Pack — VAT Period {period_start} to {period_end}"`
    4. Create RequestItems from template items
    5. Replace placeholders in descriptions: `[Q_START]` → `period_start`, `[Q_END]` → `period_end`
    6. Return RequestSet with items

**Files**:
- `backend/app/services/requests/service.py`

**Method Signature**:
```python
def create_from_template(
    self,
    engagement_id: int,
    template_id: int,
    name_override: str | None = None
) -> RequestSet:
```

---

### 2.2 Template Lookup Service
**Status**: ⏳ Pending

**Tasks**:
- [ ] Add `get_template_for_engagement()` method
  - Input: `engagement_id` or `client_type` + `engagement_type`
  - Find matching template by:
    - `client_type` match (or null for all)
    - `engagement_type` match
    - `is_active=True`
  - Return template or None

**Files**:
- `backend/app/services/requests/service.py` (or new `RequestTemplateService`)

---

### 2.3 Request Item Status Management
**Status**: ✅ Exists (basic)

**Tasks**:
- [x] Verify `RequestItemStatus` enum exists: `PENDING`, `PARTIAL`, `COMPLETE`, `WAIVED`
- [ ] Add helper method to update item status based on document count:
  - `PENDING`: No documents
  - `PARTIAL`: Some documents but < expected_count
  - `COMPLETE`: Documents >= expected_count
- [ ] Auto-update status when documents are linked/unlinked

**Files**:
- `backend/app/services/requests/service.py`

---

## Phase 3: API Layer

### 3.1 Template Endpoints
**Status**: ⏳ Pending

**Tasks**:
- [ ] Create template routes:
  - `GET /api/v1/requests/templates` — List templates (filter by client_type, engagement_type)
  - `GET /api/v1/requests/templates/{template_id}` — Get template details
  - `POST /api/v1/requests/templates/{template_id}/create-set` — Create RequestSet from template

**Files**:
- `backend/app/api/v1/requests/routes.py` (add template endpoints)
- `backend/app/schemas/requests/template.py` (new file for template schemas)

**Request Schema**:
```python
class CreateRequestSetFromTemplate(BaseModel):
    engagement_id: int
    template_id: int
    name_override: str | None = None
```

---

### 3.2 Request Set Enhancement
**Status**: ✅ Exists (basic)

**Tasks**:
- [x] Verify existing endpoints work:
  - `POST /api/v1/requests/sets` — Create set
  - `GET /api/v1/requests/sets?engagement_id={id}` — List sets
  - `GET /api/v1/requests/sets/{id}` — Get set details
- [ ] Enhance response to include:
  - Template ID if created from template
  - Completion status (items complete/pending)
  - Document counts per item

**Files**:
- `backend/app/api/v1/requests/routes.py`
- `backend/app/schemas/requests/request.py`

---

## Phase 4: Document Upload & Linking

### 4.1 Upload to Request Item
**Status**: ✅ Exists (basic)

**Tasks**:
- [x] Verify document upload can link to `request_item_id`
- [ ] Enhance upload endpoint to:
  - Auto-classify document type if not provided
  - Validate document type matches request item
  - Auto-update request item status
- [ ] Add validation: document type must match request item's document type

**Files**:
- `backend/app/api/v1/documents/routes.py`
- `backend/app/services/documents/service.py`

---

### 4.2 Client Portal Upload
**Status**: ⏳ Pending (frontend)

**Tasks**:
- [ ] Create client-facing upload page:
  - Show request set with items
  - Show progress (items complete/pending)
  - Allow upload per request item
  - Show upload token support (for email links)
- [ ] Handle "choose one" UI:
  - Show sales evidence options
  - Mark as complete when any one is uploaded

**Files**:
- `src/app/client/requests/[requestSetId]/page.tsx` (new)
- `src/app/client/upload/page.tsx` (if using token)

---

## Phase 5: Document Processing Pipeline

### 5.1 Classification
**Status**: ✅ Exists

**Tasks**:
- [x] Verify document classification works
- [ ] Enhance to validate against request item's expected document type
- [ ] Add warning if classified type doesn't match request item

**Files**:
- `backend/app/tasks/documents/document_tasks.py`
- `backend/app/services/documents/extraction.py`

---

### 5.2 Extraction & Validation
**Status**: ✅ Exists

**Tasks**:
- [x] Verify extraction pipeline works
- [x] Verify validation pipeline works
- [ ] Add validation rules specific to VAT documents:
  - Bank statements: Must cover period
  - Invoices: Must have VAT amount
  - Receipts: Must be readable (supplier, date, total, VAT)

**Files**:
- `backend/app/services/validation/service.py`

---

## Phase 6: Review & Approval

### 6.1 Document Approval
**Status**: ✅ Exists (basic)

**Tasks**:
- [x] Verify approval workflow exists (from flagged documents)
- [ ] Enhance to work with request items:
  - Show approval status per request item
  - Only approved documents count toward completion
  - Block pack export if items have unapproved documents

**Files**:
- `backend/app/api/v1/validation/routes.py`
- `src/app/accountant/components/FlaggedDocuments.tsx`

---

### 6.2 Request Item Completion Logic
**Status**: ⏳ Pending

**Tasks**:
- [ ] Add completion logic:
  - Item is "complete" when:
    - Has required number of approved documents
    - OR is waived
  - Request set is "complete" when all required items are complete
- [ ] Add API endpoint to waive request item

**Files**:
- `backend/app/services/requests/service.py`
- `backend/app/api/v1/requests/routes.py`

---

## Phase 7: Pack Builder & Export

### 7.1 Pack Builder Service
**Status**: ⏳ Pending

**Tasks**:
- [ ] Create `PackBuilderService`:
  - Input: `request_set_id`
  - Process:
    1. Get all approved documents from request items
    2. Organize by document type
    3. Create folder structure:
       ```
       VAT_Pack_{period_start}_{period_end}/
         ├── 01_Bank_Statements/
         ├── 02_Sales_Evidence/
         ├── 03_Sales_Credit_Notes/
         ├── 04_Purchase_Invoices/
         ├── 05_Purchase_Credit_Notes/
         ├── 06_Expense_Receipts/
         └── Optional/
       ```
    4. Generate summary/index file
    5. Create ZIP archive
  - Return: Pack metadata + download URL

**Files**:
- `backend/app/services/packs/builder.py` (new)
- `backend/app/services/packs/__init__.py` (new)

---

### 7.2 Pack Export API
**Status**: ⏳ Pending

**Tasks**:
- [ ] Create pack export endpoints:
  - `POST /api/v1/packs/build` — Build pack from request set
  - `GET /api/v1/packs/{pack_id}` — Get pack status
  - `GET /api/v1/packs/{pack_id}/download` — Download pack ZIP
- [ ] Add pack locking:
  - Once pack is built, lock request set
  - Prevent further document additions
  - Create pack version/snapshot

**Files**:
- `backend/app/api/v1/packs/routes.py` (new)
- `backend/app/schemas/packs/pack.py` (new)
- `backend/app/models/packs/pack.py` (new — optional, could use RequestSet status)

---

## Phase 8: Testing & Validation

### 8.1 Backend Tests
**Status**: ⏳ Pending

**Tasks**:
- [ ] Test seed script:
  - All document types created
  - Template created with correct items
  - "Choose one" handled correctly
- [ ] Test service methods:
  - `create_from_template()` creates correct structure
  - Placeholder replacement works
  - Status updates work
- [ ] Test API endpoints:
  - Template lookup
  - Request set creation
  - Document linking
  - Pack building

**Files**:
- `backend/tests/scripts/test_seed_vat_st_pack.py` (new)
- `backend/tests/services/test_request_template_service.py` (new)
- `backend/tests/api/v1/test_packs.py` (new)

---

### 8.2 Integration Tests
**Status**: ⏳ Pending

**Tasks**:
- [ ] End-to-end flow test:
  1. Create engagement
  2. Create request set from template
  3. Upload documents
  4. Process documents
  5. Approve documents
  6. Build pack
  7. Download pack

**Files**:
- `backend/tests/integration/test_vat_pack_flow.py` (new)

---

## Phase 9: Frontend Implementation

### 9.1 Accountant UI
**Status**: ⏳ Pending

**Tasks**:
- [ ] Add "Create Request Set" button on engagement page
  - Show template selector
  - Auto-select based on client type + engagement type
- [ ] Request set detail page:
  - Show all items with status
  - Show document counts
  - Show "Build Pack" button (enabled when complete)
- [ ] Pack builder UI:
  - Show pack structure preview
  - Show included/excluded documents
  - Download button

**Files**:
- `src/app/accountant/engagements/[engagementId]/page.tsx`
- `src/app/accountant/requests/[requestSetId]/page.tsx` (new)
- `src/app/accountant/packs/[packId]/page.tsx` (new)

---

### 9.2 Client Portal UI
**Status**: ⏳ Pending

**Tasks**:
- [ ] Request set view:
  - Show items with descriptions
  - Show upload progress
  - Upload button per item
  - "Choose one" UI for sales evidence
- [ ] Upload interface:
  - Drag & drop
  - File validation
  - Progress indicators

**Files**:
- `src/app/client/requests/[requestSetId]/page.tsx` (new)
- `src/app/client/upload/page.tsx` (if using token)

---

## Implementation Order

### Sprint 1: Foundation
1. ✅ Complete seed script
2. Run seed script
3. Add `create_from_template()` service method
4. Add template API endpoints
5. Test template → request set creation

### Sprint 2: Upload & Processing
1. Enhance document upload to link to request items
2. Add request item status auto-update
3. Test document upload flow
4. Verify classification/extraction works

### Sprint 3: Review & Approval
1. Enhance approval workflow for request items
2. Add completion logic
3. Test approval flow

### Sprint 4: Pack Builder
1. Create PackBuilderService
2. Add pack export API
3. Test pack building
4. Add pack locking

### Sprint 5: Frontend
1. Accountant UI for request sets
2. Client portal upload UI
3. Pack builder UI
4. End-to-end testing

---

## Key Design Decisions

### 1. "Choose One" Handling
- **Decision**: Create 3 separate template items, all `is_required=False`
- **Rationale**: Simplifies UI and logic; client can upload any one
- **Alternative Considered**: Single item with type variants (more complex)

### 2. Placeholder Replacement
- **Decision**: Replace `[Q_START]` and `[Q_END]` when creating request set
- **Rationale**: Makes descriptions specific to period
- **Implementation**: In `create_from_template()` method

### 3. Pack Locking
- **Decision**: Lock request set when pack is built
- **Rationale**: Ensures pack integrity; accountant can unlock if needed
- **Implementation**: Set `RequestSet.status = LOCKED` or add `is_locked` flag

### 4. Document Approval
- **Decision**: Only approved documents go into pack
- **Rationale**: Ensures quality; accountant has final say
- **Implementation**: Filter by `validation_result.review_action = "approve"`

---

## Dependencies

- ✅ Document types system exists
- ✅ Request template system exists
- ✅ Document upload/processing exists
- ✅ Validation/approval system exists
- ⏳ Pack builder (new)
- ⏳ Template-to-request-set service (new)

---

## Notes

- The seed script handles the "choose one" by creating 3 separate items
- Period placeholders (`[Q_START]`, `[Q_END]`) are replaced when creating request set
- All optional items are marked `is_required=False`
- Pack building only includes approved documents
- Request set can be locked after pack is built
