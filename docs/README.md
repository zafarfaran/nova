<p align="center">
  <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNm5qY2VjenM5MnZwZHI4cmd3MTFia2tybnZsMjk2cGxtZHN2anhzdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TbXVwz9MDnwYst8GXj/giphy.gif" alt="Nova GIF" />
</p>

<h1 align="center">Nova — 10x Your Accounting Power</h1>

<p align="center">
  <strong>Stop chasing paperwork. Nova helps accountants collect, process, and validate client documents faster using AI.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-15-black?style=flat&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-Python-009688?style=flat&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/AI-Claude%20%2B%20GPT-5A67D8?style=flat" alt="AI Powered" />
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat&logo=supabase" alt="Supabase" />
</p>

---

## 📚 Table of Contents

- [What is Nova?](#-what-is-nova)
- [Key Features](#-key-features)
- [Tech Stack](#️-tech-stack)
- [Architecture](#️-architecture)
- [Database Schema](#-database-schema)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [AI Chat Tools](#-ai-chat-tools)
- [Monitoring & Metrics](#-monitoring--metrics)
- [Roadmap](#-roadmap)

---

## ⚡ What is Nova?

Nova is an **AI-powered document management platform** designed for accountants to speed up client documentation across multiple engagement types:

| Engagement Type | What Nova Helps With |
|-----------------|---------------------|
| 📊 **VAT Returns** | Collect and validate invoices, receipts, bank statements |
| 📑 **Tax Returns** | Gather P60s, dividend vouchers, rental income docs |
| 📈 **Annual Accounts** | Organize financial records, bank reconciliations |
| 🔍 **Audits** | Track evidence collection and compliance |
| 📒 **Bookkeeping** | Manage ongoing document flow from clients |

### The Problem

- Accountants spend **hours** chasing clients for documents
- Manual data entry from invoices and receipts is tedious
- VAT validation errors get caught at the last minute
- No visibility into which clients are on track

### The Nova Solution

- **AI extracts data** from invoices, receipts, and bank statements automatically
- **Smart chaser emails** remind clients about missing documents
- **Built-in validation** catches errors before submission
- **Real-time dashboard** shows client status at a glance

---

## 🚀 Key Features

### 📄 AI-Powered Document Processing
- **Automatic extraction** — Invoice numbers, dates, amounts, VAT, supplier info
- **PDF + Image support** — Handles scans, photos, and digital documents
- **Multi-version tracking** — Keep history of document changes
- **Batch processing** — Process all documents for an engagement at once

### ✅ Built-in Compliance Validation
- **VAT number format** — UK VAT number validation
- **Rate validation** — Checks against valid UK VAT rates (0%, 5%, 20%)
- **Totals matching** — Net + VAT = Gross verification
- **Duplicate detection** — Catches potential duplicate invoices
- **AI anomaly detection** — Claude-powered unusual pattern detection

### 📋 Document Request System
- **Request sets** — Group document requests by engagement
- **Status tracking** — Pending → Partial → Complete
- **Assignment** — Assign requests to specific client contacts
- **Templates** — Reusable request templates by engagement type

### 📧 Automated Chasers
- **AI-generated emails** — Personalized, professional chaser messages
- **Secure upload portal** — Clients upload via unique token links
- **Reminder tracking** — Automatic follow-ups for missing documents
- **Response logging** — Track what clients have submitted

### 💬 AI Chat Assistant
- **Natural language queries** — "Which clients have missing documents?"
- **Tool calling** — Search clients, view checklists, send emails
- **Streaming responses** — Real-time AI responses
- **Session history** — Persistent chat conversations

### 🔍 Full Audit Trail
- **Entity tracking** — Log changes to any record
- **Actor tracking** — Who made what changes
- **Change history** — JSON diff of modifications

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 15** | React framework with App Router |
| **TypeScript** | Type-safe development |
| **Tailwind CSS** | Utility-first styling |
| **NextAuth.js** | Authentication |
| **Prisma** | Database ORM for frontend |

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance Python API |
| **SQLAlchemy** | ORM with relationship support |
| **Pydantic** | Data validation and settings |
| **Alembic** | Database migrations |

### AI & Processing
| Technology | Purpose |
|------------|---------|
| **Anthropic Claude** | Primary AI for extraction & analysis |
| **OpenAI GPT-4** | Fallback and specialized tasks |
| **pdfplumber** | PDF text extraction |
| **Vision APIs** | Image-based OCR |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Supabase** | Managed PostgreSQL + Auth + Storage |
| **UploadThing / S3** | File storage options |
| **SMTP** | Email delivery |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Dashboard   │  │  Onboarding  │  │   AI Chat    │  │   Auth       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
│                              │                                               │
│                         Prisma ORM                                           │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPABASE (PostgreSQL)                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  clients │ engagements │ documents │ request_sets │ audit_logs │ ...   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND (FastAPI)                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Clients    │  │ Engagements  │  │  Documents   │  │  Validation  │     │
│  │   Service    │  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Requests   │  │   Chasers    │  │    Chat      │  │    Email     │     │
│  │   Service    │  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      AI PROCESSING LAYER                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │ PDF Extract │  │ AI Vision   │  │ Validation  │                  │    │
│  │  │ (pdfplumber)│  │ (Claude)    │  │ (Rules+AI)  │                  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

Nova uses an **enterprise-grade schema** designed for multi-client, multi-engagement workflows:

```mermaid
erDiagram
    clients ||--o{ client_contacts : has
    clients ||--o{ engagements : has
    clients ||--o{ counterparties : has
    clients ||--o{ financial_accounts : has
    clients ||--o{ documents : owns
    
    engagements ||--o{ documents : contains
    engagements ||--o{ request_sets : has
    engagements ||--o{ audit_logs : logs
    
    request_sets ||--o{ request_items : contains
    request_items }o--o{ documents : satisfied_by
    
    document_categories ||--o{ document_types : groups
    document_types ||--o{ documents : typed_as
    documents ||--o{ document_versions : versioned
    file_objects ||--o{ document_versions : stores
```

### Core Entities

| Entity | Purpose |
|--------|---------|
| **clients** | Businesses (sole traders, limited companies, etc.) |
| **client_contacts** | Multiple contacts per client |
| **engagements** | Work periods (VAT return Q1 2026, Annual Accounts 2025) |
| **documents** | Uploaded files with extracted data |
| **document_versions** | Version history with extraction results |
| **document_types** | Configurable document categories |
| **request_sets** | Grouped document requests |
| **request_items** | Individual document requests |
| **counterparties** | Suppliers and customers |
| **financial_accounts** | Bank accounts, credit cards |
| **audit_logs** | Complete change history |

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account (or local PostgreSQL)

### 1. Clone & Install

```bash
git clone https://github.com/your-org/nova.git
cd nova

# Frontend
npm install

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup

Create `.env` in root:
```env
# Database (Supabase)
DATABASE_URL="postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"
DIRECT_URL="postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"
SUPABASE_DATA_URL="postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"

# AI
ANTHROPIC_API_KEY="sk-ant-..."
OPENAI_API_KEY="sk-..."

# Storage
STORAGE_PROVIDER="uploadthing"
UPLOADTHING_TOKEN="..."

# Email
SMTP_HOST="smtp.ionos.co.uk"
SMTP_PORT=587
SMTP_USERNAME="..."
SMTP_PASSWORD="..."
SMTP_FROM_EMAIL="nova@yourdomain.com"
```

### 3. Database Setup

```bash
# Generate Prisma client (frontend)
npx prisma generate

# Run Alembic migrations (backend)
cd backend
alembic upgrade head
```

### 4. Run Development Servers

```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend
cd backend
uvicorn app.main:app --reload --port 8000
```

---

## 📁 Project Structure

```
nova/
├── src/                      # Next.js frontend
│   ├── app/                  # App Router pages
│   │   ├── accountant/       # Dashboard views
│   │   ├── onboard/          # Client onboarding
│   │   └── api/              # API routes
│   └── server/               # Server utilities
│
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── ai/              # AI providers & tools
│   │   └── tasks/           # Background tasks
│   └── alembic/             # Database migrations
│
├── prisma/                   # Prisma schema (frontend ORM)
└── generated/               # Generated Prisma client
```

---

## 🔌 API Endpoints

### Clients
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/clients` | Create client |
| GET | `/api/v1/clients` | List clients |
| GET | `/api/v1/clients/{id}` | Get client |
| PATCH | `/api/v1/clients/{id}` | Update client |
| DELETE | `/api/v1/clients/{id}` | Delete client |

### Engagements
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/engagements` | Create engagement |
| GET | `/api/v1/engagements` | List engagements |
| GET | `/api/v1/engagements/{id}` | Get engagement |
| PATCH | `/api/v1/engagements/{id}` | Update engagement |
| POST | `/api/v1/engagements/{id}/lock` | Lock engagement |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload document |
| POST | `/api/v1/documents/sync` | Sync from storage |
| GET | `/api/v1/documents` | List documents |
| POST | `/api/v1/documents/{id}/process` | Process document |
| GET | `/api/v1/documents/{id}/extracted-data` | Get extracted data |

### Validation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/validation/run/{doc_id}` | Run validation |
| GET | `/api/v1/validation/results/{doc_id}` | Get results |
| GET | `/api/v1/validation/summary/{engagement_id}` | Get summary |

### Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/requests/sets` | Create request set |
| POST | `/api/v1/requests/items` | Create request item |
| POST | `/api/v1/requests/items/{id}/documents/{doc_id}` | Link document |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/sessions` | Create session |
| POST | `/api/v1/chat/sessions/{id}/chat` | Send message |
| POST | `/api/v1/chat/stream` | Stream response |

---

## 🤖 AI Chat Tools

Nova's chat assistant can perform actions through tool calling:

| Tool | Description |
|------|-------------|
| `list_clients` | List all clients |
| `search_clients` | Search by name/email |
| `get_client_details` | Full client profile |
| `get_document_checklist` | Document status for client |
| `get_clients_needing_attention` | Flag at-risk clients |
| `create_client` | Add new client |
| `update_checklist_item` | Update request status |
| `send_document_request_email` | Send chaser email |

---

## 📊 Monitoring & Metrics

Nova includes a comprehensive metrics and logging system with Prometheus and Grafana integration.

### Quick Start

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
# Metrics: http://localhost:8000/metrics
```

### Features

- ✅ **Always-on Metrics**: HTTP requests, LLM calls, costs, and business metrics
- ✅ **Configurable Logging**: Per-section logging with verbosity control
- ✅ **Request Tracking**: End-to-end request tracking with unique IDs
- ✅ **Cost Tracking**: Real-time LLM cost calculation
- ✅ **Structured Logging**: JSON-formatted logs

### Configuration

```bash
# Enable logging for specific sections
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all

# Set verbosity per section
LOGGING_LEVELS=document_processing:DEBUG,chat:INFO
```

### Documentation

- **[Full Documentation](backend/METRICS_LOGGING_README.md)** - Comprehensive guide
- **[Quick Reference](backend/METRICS_QUICK_REFERENCE.md)** - Quick reference guide
- **[Configuration Guide](backend/METRICS_CONFIG.md)** - Configuration details

---

## 🗺️ Roadmap

### ✅ Completed
- [x] Enterprise schema with engagements
- [x] Document request system
- [x] AI-powered extraction
- [x] Validation engine
- [x] Chaser email system
- [x] AI chat assistant
- [x] Supabase migration

### 🚧 In Progress
- [ ] Client portal for document uploads
- [ ] Dashboard UI improvements
- [ ] Bulk operations

### 📋 Planned
- [ ] HMRC MTD integration
- [ ] Bank feed integration
- [ ] Mobile app
- [ ] Team collaboration features
- [ ] White-label support

---

<p align="center">
  <strong>Built with ❤️ by the Nova Team</strong><br>
  Powered by Claude AI | Making accountants unstoppable since 2026
</p>
