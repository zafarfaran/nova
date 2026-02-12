# VAT Sole Trader Pack — Database Schema & Workflow Diagrams

## Database Schema (ER Diagram)

```mermaid
erDiagram
    Client ||--o{ Engagement : has
    Client {
        int id PK
        string name
        string client_type "sole_trader | limited_company"
        string vat_number
        string entity_type
    }
    
    Engagement ||--o{ RequestSet : has
    Engagement {
        int id PK
        int client_id FK
        string engagement_type "vat_return | annual_accounts"
        date period_start
        date period_end
        string status
    }
    
    RequestTemplate ||--o{ RequestTemplateItem : contains
    RequestTemplate {
        int id PK
        string name
        string client_type "sole_trader | limited_company | null"
        string engagement_type "vat_return | annual_accounts | null"
        boolean is_active
    }
    
    RequestTemplateItem {
        int id PK
        int template_id FK
        int document_type_id FK
        string description "with [Q_START] and [Q_END] placeholders"
        int expected_count
        boolean is_required
        int order_index
    }
    
    RequestSet ||--o{ RequestItem : contains
    RequestSet {
        int id PK
        int engagement_id FK
        string name "e.g., 'VAT Sole Trader Pack — VAT Period 2024-01-01 to 2024-03-31'"
        string status "draft | sent | partial | complete | expired"
        date due_date
        string upload_token
        date sent_at
    }
    
    RequestItem ||--o{ Document : "links to (many-to-many)"
    RequestItem {
        int id PK
        int request_set_id FK
        int document_type_id FK
        string description "placeholders replaced with actual dates"
        int expected_count
        boolean is_required
        string status "pending | partial | complete | waived"
        date due_date
    }
    
    DocumentCategory ||--o{ DocumentType : contains
    DocumentCategory {
        int id PK
        string code "BANKING | SALES | PURCHASES | VAT | etc."
        string name
    }
    
    DocumentType ||--o{ RequestItem : "used by"
    DocumentType ||--o{ RequestTemplateItem : "used by"
    DocumentType ||--o{ Document : "classifies"
    DocumentType {
        int id PK
        int category_id FK
        string code "ST_VAT_BANK_STATEMENTS_ALL_ACCOUNTS | etc."
        string name
        string client_type_scope "sole_trader | limited_company | null"
        boolean requires_counterparty
        boolean requires_account
        boolean requires_engagement
    }
    
    Document {
        int id PK
        int client_id FK
        int engagement_id FK
        int document_type_id FK
        string filename
        string s3_key
        string status "pending | processing | extracted | validated | failed"
        date document_date
    }
    
    RequestTemplateItem }o--|| DocumentType : "references"
    RequestItem }o--|| DocumentType : "references"
    RequestItem }o--o{ Document : "many-to-many via request_item_documents"
```

## Workflow: Creating RequestSet from Template

```mermaid
sequenceDiagram
    participant Accountant
    participant API as API Endpoint
    participant Service as RequestSetService
    participant DB as Database
    participant Template as RequestTemplate
    participant Engagement as Engagement
    
    Accountant->>API: POST /api/v1/requests/templates/{id}/create-set<br/>{engagement_id, template_id}
    
    API->>Service: create_from_template(engagement_id, template_id)
    
    Service->>DB: Get Engagement (with Client relationship)
    DB-->>Service: Engagement + Client
    
    Service->>DB: Get RequestTemplate (with Items)
    DB-->>Service: Template + TemplateItems
    
    Service->>Service: Validate:<br/>- client_type matches<br/>- engagement_type matches<br/>- template is_active
    
    alt Validation fails
        Service-->>API: ValueError
        API-->>Accountant: 400 Bad Request
    else Validation passes
        Service->>Service: Generate name:<br/>"{template.name} — VAT Period {start} to {end}"
        
        Service->>DB: Create RequestSet
        DB-->>Service: RequestSet (id)
        
        loop For each TemplateItem
            Service->>Service: Replace placeholders:<br/>[Q_START] → period_start<br/>[Q_END] → period_end
            
            Service->>DB: Create RequestItem<br/>(from TemplateItem)
        end
        
        Service->>DB: Commit transaction
        Service-->>API: RequestSet with Items
        API-->>Accountant: 201 Created + RequestSet
    end
```

## Workflow: Client Uploads Document

```mermaid
sequenceDiagram
    participant Client
    participant Portal as Client Portal
    participant API as Documents API
    participant DocService as DocumentService
    participant RequestService as RequestItemService
    participant DB as Database
    participant Storage as S3/UploadThing
    participant AI as AI Processing
    
    Client->>Portal: Upload file for RequestItem
    Portal->>API: POST /api/v1/documents/upload<br/>?request_item_id={id}
    
    API->>DocService: upload(file, client_id, engagement_id)
    
    DocService->>DocService: Compute file hash
    DocService->>DB: Check for duplicates
    DB-->>DocService: No duplicate found
    
    DocService->>Storage: Upload file
    Storage-->>DocService: s3_key
    
    DocService->>DB: Create Document record
    DB-->>DocService: Document (id)
    
    API->>DB: Get RequestItem
    DB-->>API: RequestItem
    
    API->>API: Validate document_type matches<br/>(warn if mismatch, don't fail)
    
    API->>DB: Link Document to RequestItem<br/>(many-to-many)
    
    API->>RequestService: _update_item_status(request_item)
    RequestService->>RequestService: Calculate status:<br/>- 0 docs → PENDING<br/>- < expected → PARTIAL<br/>- >= expected → COMPLETE
    
    RequestService->>DB: Update RequestItem.status
    DB-->>RequestService: Updated
    
    API->>AI: Queue document for processing<br/>(background task)
    
    API-->>Portal: 200 OK + Document info
    Portal-->>Client: Upload successful
```

## Workflow: Document Processing & Approval

```mermaid
sequenceDiagram
    participant AI as AI Processor
    participant DB as Database
    participant Doc as Document
    participant Validation as ValidationService
    participant Accountant
    participant ReviewAPI as Review API
    
    AI->>Doc: process_document()
    Doc->>Doc: Extract text & structure
    Doc->>Doc: Classify document type
    Doc->>Doc: Extract fields (invoice number, dates, amounts, etc.)
    Doc->>DB: Update Document.status = EXTRACTED
    
    Doc->>Validation: validate_document()
    Validation->>Validation: Run validation rules
    Validation->>DB: Create ValidationResult<br/>(status: passed | failed | warning)
    
    alt Validation issues found
        Validation->>DB: ValidationResult.status = FAILED/WARNING
        DB-->>Accountant: Flagged for review
    end
    
    Accountant->>ReviewAPI: POST /api/flagged-documents/{id}/review<br/>{action: "approve" | "reject" | "request_info"}
    
    ReviewAPI->>DB: Update ValidationResult<br/>review_action, reviewed_at, reviewed_by
    DB-->>ReviewAPI: Updated
    
    ReviewAPI-->>Accountant: Review recorded
```

## Workflow: Request Item Status Flow

```mermaid
stateDiagram-v2
    [*] --> PENDING: RequestItem created
    
    PENDING --> PARTIAL: Document linked<br/>(count < expected)
    PENDING --> COMPLETE: Document linked<br/>(count >= expected)
    
    PARTIAL --> COMPLETE: More documents linked<br/>(count >= expected)
    PARTIAL --> PENDING: Document unlinked<br/>(count = 0)
    
    COMPLETE --> PARTIAL: Document unlinked<br/>(count < expected)
    COMPLETE --> PENDING: All documents unlinked<br/>(count = 0)
    
    PENDING --> WAIVED: Accountant waives item
    PARTIAL --> WAIVED: Accountant waives item
    COMPLETE --> WAIVED: Accountant waives item
    
    note right of PENDING
        No documents linked
    end note
    
    note right of PARTIAL
        Some documents linked
        but not enough
    end note
    
    note right of COMPLETE
        Required number of
        documents linked
    end note
```

## Complete System Flow: End-to-End

```mermaid
flowchart TD
    Start([Accountant creates Engagement]) --> CreateClient{Client exists?}
    CreateClient -->|No| NewClient[Create Client<br/>with client_type='sole_trader']
    NewClient --> CreateEngagement
    CreateClient -->|Yes| CreateEngagement[Create Engagement<br/>engagement_type='vat_return'<br/>period_start, period_end]
    
    CreateEngagement --> GetTemplate[Get RequestTemplate<br/>client_type='sole_trader'<br/>engagement_type='vat_return']
    
    GetTemplate --> CreateRequestSet[Create RequestSet from Template<br/>- Replace [Q_START] and [Q_END]<br/>- Create RequestItems from TemplateItems]
    
    CreateRequestSet --> SendRequest[Send RequestSet to Client<br/>via email/portal]
    
    SendRequest --> ClientUploads[Client uploads documents<br/>via portal]
    
    ClientUploads --> LinkDoc[Link Document to RequestItem<br/>- Validate document_type<br/>- Auto-update RequestItem.status]
    
    LinkDoc --> ProcessDoc[AI processes document<br/>- Classify<br/>- Extract<br/>- Validate]
    
    ProcessDoc --> Review{Validation<br/>issues?}
    
    Review -->|Yes| AccountantReview[Accountant reviews<br/>flagged documents]
    Review -->|No| AutoApproved[Document auto-approved]
    
    AccountantReview --> Approve{Approve?}
    Approve -->|Yes| Approved
    Approve -->|No| Rejected[Document rejected<br/>Client must re-upload]
    Rejected --> ClientUploads
    
    Approved --> CheckComplete{All required<br/>RequestItems<br/>complete?}
    AutoApproved --> CheckComplete
    
    CheckComplete -->|No| ClientUploads
    CheckComplete -->|Yes| BuildPack[Build Pack<br/>- Only approved documents<br/>- Organize by type<br/>- Create ZIP]
    
    BuildPack --> LockPack[Lock RequestSet<br/>status = LOCKED]
    LockPack --> Export[Export Pack<br/>for submission]
    
    Export --> End([Pack ready for HMRC])
    
    style CreateRequestSet fill:#e1f5ff
    style LinkDoc fill:#fff4e1
    style ProcessDoc fill:#ffe1f5
    style BuildPack fill:#e1ffe1
```

## Key Relationships Summary

### Template → RequestSet Creation
- **RequestTemplate** defines the structure (document types, descriptions, order)
- **RequestTemplateItem** has placeholders: `[Q_START]` and `[Q_END]`
- When creating **RequestSet** from template:
  - Placeholders are replaced with actual dates from **Engagement**
  - Each **RequestTemplateItem** becomes a **RequestItem**
  - **RequestItem** links to the same **DocumentType** as the template item

### Document → RequestItem Linking
- **Document** can be linked to multiple **RequestItems** (many-to-many)
- When document is linked:
  - **RequestItem.status** auto-updates based on document count
  - Document type validation (warns if mismatch, doesn't fail)
- When document is unlinked:
  - **RequestItem.status** updates back

### Status Progression
- **RequestItem**: `PENDING` → `PARTIAL` → `COMPLETE` (or `WAIVED`)
- **RequestSet**: `DRAFT` → `SENT` → `PARTIAL` → `COMPLETE` (or `EXPIRED`)
- **Document**: `PENDING` → `PROCESSING` → `EXTRACTED` → `VALIDATED` (or `FAILED`)

### "Choose One" Pattern
For sales evidence, the template creates **3 separate RequestItems**:
- `ST_VAT_SALES_INVOICES` (is_required=False)
- `ST_VAT_SALES_POS_SUMMARY` (is_required=False)
- `ST_VAT_SALES_CASHBOOK` (is_required=False)

Client can upload **any one** of these, and the system will mark the request as satisfied.
