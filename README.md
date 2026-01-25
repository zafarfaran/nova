![Nova GIF](https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNm5qY2VjenM5MnZwZHI4cmd3MTFia2tybnZsMjk2cGxtZHN2anhzdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TbXVwz9MDnwYst8GXj/giphy.gif)

# Nova — VAT Compliance for Accountants

Nova is a VAT evidence collection and review platform that makes accountants' lives easier. It combines a React/Next.js dashboard with a FastAPI backend to ingest documents, run AI extraction and validation, and provide a human‑review workflow that can move clients to “Ready to submit.”

## Highlights
- Multimodal document extraction (PDF + image) with AI providers (OpenAI/Anthropic).
- Rule‑based and AI anomaly validation with a review queue.
- Final review controls to mark VAT periods as **Ready**.
- AI chat with custom tools for client and document operations.

## Novel Approaches
- **Dual‑path validation**: deterministic rules + AI anomaly detection, with human approval closing the loop.
- **Multimodal extraction pipeline**: PDF structure + vision extraction converge into normalized fields for validators.
- **Document‑level resolution**: approve/reject all issues on a document to reduce review fatigue.
- **Flow‑aware UX**: client stage changes are driven by validation and review state, not just uploads.
- **Audit‑first workflows**: review actions write audit entries for traceability.

## Architecture Diagram (Multimodal + Custom Functions)

```mermaid
flowchart LR
  subgraph Frontend[Next.js App Router]
    UI[Accountant Dashboard]
    Chat[AI Chat UI (SSE)]
    API[Next.js API Routes]
  end

  subgraph Storage[Storage]
    UT[UploadThing / S3]
  end

  subgraph Backend[FastAPI Backend]
    Sync[Document Sync API]
    Tasks[Background Tasks]
    Validate[Validation Service]
    ChatSvc[Chat Service]
  end

  subgraph Multimodal[Multimodal Extraction]
    PDF[PDF Extraction (pdfplumber)]
    IMG[Image Extraction / Vision]
    LLM[AI Providers (OpenAI / Anthropic)]
  end

  subgraph DB[(PostgreSQL)]
    Docs[Documents]
    Val[Validation Results]
    Periods[VAT Periods]
  end

  UI --> API
  API --> UT
  API --> Sync
  Sync --> Tasks
  Tasks --> PDF
  Tasks --> IMG
  PDF --> LLM
  IMG --> LLM
  LLM --> Docs
  Docs --> Validate
  Validate --> Val
  Val --> Docs
  Docs --> Periods

  Chat --> ChatSvc
  ChatSvc --> Tools[Custom Tools]
  Tools --> DB

  subgraph Tools[Custom Functions]
    T1[list_clients]
    T2[get_client_details]
    T3[search_clients]
    T4[get_document_checklist]
    T5[get_clients_needing_attention]
    T6[create_client]
    T7[update_checklist_item]
  end
```

## Custom AI Tools (Chat Function Calling)
These tools back the AI assistant and the interactive UI cards:
- `list_clients` — list all clients.
- `get_client_details` — details including document and bank status.
- `search_clients` — find clients by name/email.
- `get_document_checklist` — checklist status for a client.
- `get_clients_needing_attention` — missing documents + validation + review status.
- `create_client` — create a new client + VAT period + checklist.
- `update_checklist_item` — update checklist status.

## Core Data Flow
1. **Upload** → files uploaded via UploadThing (or S3).
2. **Sync** → Next.js `/api/sync-document` syncs the document into the backend.
3. **Extract** → FastAPI background tasks run multimodal extraction:
   - PDF: `pdfplumber` structure + LLM extraction.
   - Images: vision extraction via AI providers.
4. **Normalize** → extracted data flattened for validators.
5. **Validate** → rule-based checks + AI anomaly detection.
6. **Review** → flagged items reviewed by accountants.
7. **Finalize** → “Mark Ready” moves VAT period to `READY`.

## Project Structure (Top-Level)
```
src/app/            Next.js UI + API routes
backend/app/        FastAPI backend + services + tasks
prisma/             Prisma schema
public/             Static assets (logo.svg)
```

## Environment Variables
Frontend (`src/env.js`):
- `DATABASE_URL` (required)
- `AUTH_SECRET` (optional in dev)
- `NEXT_PUBLIC_API_URL` (optional; defaults to localhost:8000)

Backend (`backend/app/config.py`):
- `DATABASE_URL` or `DATABASE_PATH`
- `AI_PROVIDER` (`openai` or `anthropic`)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
- `UPLOADTHING_TOKEN` (if using UploadThing)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME` (if using S3)

## Running Locally
Frontend:
```
npm install
npm run dev
```

Backend:
```
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Key API Endpoints (Frontend)
- `/api/documents/[clientId]` — document list + validation summary.
- `/api/flagged-documents` — flagged validation results.
- `/api/flagged-documents/[docId]/review` — review actions (single or bulk).
- `/api/vat-periods/[periodId]/status` — mark VAT period `READY`.

## Notes
- The dashboard uses Prisma; the backend uses SQLAlchemy against the same database.
- Approved validation issues are treated as resolved in summaries and flow stages.

## License
Internal project — not licensed for public distribution.
