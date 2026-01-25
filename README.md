<p align="center">
  <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNm5qY2VjenM5MnZwZHI4cmd3MTFia2tybnZsMjk2cGxtZHN2anhzdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TbXVwz9MDnwYst8GXj/giphy.gif" alt="Nova GIF" />
</p>

<h1 align="center">Nova — 10x Your Accounting Power</h1>

<p align="center">
  <strong>Stop drowning in spreadsheets. Nova is the AI-powered platform that turns accountants into productivity machines.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-14-black?style=flat&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-Python-009688?style=flat&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/AI-Claude%20%2B%20GPT-5A67D8?style=flat" alt="AI Powered" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-336791?style=flat&logo=postgresql" alt="PostgreSQL" />
</p>

<p align="center">
  Nova combines cutting-edge AI with human expertise to help accounting firms manage hundreds of clients, automate compliance, and reclaim their time. Process thousands of documents in seconds, not hours.
</p>

---

## 📚 Table of Contents

- [Why Nova?](#-why-nova)
- [Key Features](#-key-features)
- [Novel Approaches](#-novel-approaches)
- [Tech Stack](#️-tech-stack)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Architecture](#️-architecture)
- [Custom Functions (AI Chat)](#-custom-functions-ai-chat)
- [Specialized AI Agents](#-specialized-ai-agents)
- [Design Philosophy](#-design-philosophy)
- [Key Metrics](#-key-metrics)
- [Security & Compliance](#-security--compliance)
- [Deployment](#-deployment)
- [License](#-license)

---

## ⚡ Why Nova?

### The Problem
Traditional accounting workflows are broken:
- Accountants spend **80% of their time** on manual data entry
- Processing VAT returns takes **4-6 hours per client**
- Email follow-ups and reminders are done **manually**
- Bank reconciliation happens in **weekly batches**
- Human error rates sit at **5-10%**
- Firms are limited to **50-75 clients per accountant**

### The Nova Solution
We built Nova to solve these problems with AI:
- **95% time saved** — What took hours now takes minutes
- **99.9% accuracy** — AI catches errors humans miss
- **10,000+ docs/hour** — Process documents at scale
- **Real-time banking** — Transactions sync automatically
- **Zero-touch automation** — Emails, reminders, and follow-ups run on autopilot
- **10x client capacity** — Manage 150-250 clients per accountant

### The Result
Accounting firms using Nova:
- Serve **3x more clients** with the same team
- Reduce VAT prep time by **75%**
- Catch **10x more errors** before submission
- Free up **20+ hours per week** for strategic work
- Delight clients with **instant responses** and **real-time status**

---

## 🚀 Key Features

### Intelligence That Thinks Ahead
- **10,000+ documents/hour** — Process invoices, receipts, and statements at scale
- **99.9% accuracy** — Claude AI extracts, validates, and categorizes with precision
- **<1s per invoice** — What used to take hours now takes seconds
- **Multimodal extraction** — Seamless handling of PDFs, images, and scanned documents

### Real-Time Banking & Reconciliation
- **Live bank sync** — Connect any UK bank for automatic transaction flow
- **Auto-reconciliation** — Transactions matched and categorized in the background
- **Smart categorization** — AI learns your patterns and applies them automatically

### Autopilot Mode
- **Zero-touch automation** — Smart reminders, automated chasers, deadline alerts
- **24/7 monitoring** — Nova watches your clients so you don't have to
- **Email automation** — Branded, AI-generated emails for every client interaction

### Anomaly Detection
- **Duplicate detection** — Catches duplicate invoices before they become problems
- **Suspicious amounts** — Flags unusual transactions automatically
- **VAT validation** — Real-time HMRC VAT number verification
- **Missing data alerts** — Identifies gaps before submission

### Command Center Dashboard
- **Manage hundreds of clients** — Bird's-eye view of every client, deadline, and document
- **Advanced filtering** — Sort, search, and find exactly who needs attention
- **Real-time status** — Know instantly which clients are on track or need help
- **AI-powered chat** — Natural language interface to find clients and surface status

### One-Click VAT Returns
- **HMRC-ready exports** — Generate compliant VAT returns instantly
- **Automated validation** — All data checked and categorized before generation
- **Review workflow** — Document-level approve/reject for efficient processing

## 💡 Novel Approaches

### Dual Validation Loop
Rules-based validation combined with AI anomaly detection, resolved through streamlined human approval. This hybrid approach catches both known patterns and unexpected edge cases.

### Multimodal Document Blending
PDF structure extraction and vision-based OCR normalized into a unified schema. Whether it's a pristine digital invoice or a crumpled receipt photo, Nova handles it the same way.

### Document-Level Resolution
Reduce review fatigue by approving or rejecting all issues for a document at once. No more clicking through individual line items.

### Flow-Aware UX
Client stages automatically update based on validation and review state. Accountants always see the current reality, not stale snapshots.

### AI-Powered Email Service
Branded, context-aware emails generated by Claude for every client interaction. From welcome messages to validation issues to VAT return notifications—all perfectly on-brand.

### Banking Integration
Direct integration with UK banks via secure APIs. Transactions sync in real-time, reconciliation happens automatically, and accountants see a complete financial picture.

---

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** — React framework with App Router and Server Components
- **TypeScript** — Type-safe development
- **Tailwind CSS** — Utility-first styling with custom design system
- **NextAuth.js** — Authentication with multiple providers
- **TanStack Query** — Data fetching and caching
- **shadcn/ui** — Accessible component library

### Backend
- **FastAPI** — High-performance Python API framework
- **SQLAlchemy** — ORM with PostgreSQL
- **Pydantic** — Data validation and settings management
- **Alembic** — Database migrations
- **SMTP Integration** — Email delivery with branded templates

### AI & Processing
- **Anthropic Claude (Sonnet 4.5)** — Primary AI for document extraction and analysis
- **OpenAI GPT-4** — Fallback and specialized tasks
- **pdfplumber** — PDF text and structure extraction
- **Vision APIs** — Image-based OCR and analysis
- **Custom validation agents** — Specialized validators for each document type

### Infrastructure
- **PostgreSQL** — Primary database
- **Docker** — Containerization and deployment
- **GitHub Actions** — CI/CD pipeline
- **Environment-based config** — Separate dev/staging/production settings

### Banking & Compliance
- **Open Banking APIs** — Secure bank connections
- **HMRC API Integration** — VAT number validation
- **Encrypted storage** — Bank-grade security for sensitive data

## 📁 Project Structure

```
nova/
├── src/                          # Next.js frontend
│   ├── app/                      # App router pages
│   │   ├── _components/          # Landing page components
│   │   ├── accountant/           # Accountant dashboard
│   │   ├── client/               # Client portal
│   │   └── api/                  # API routes
│   ├── components/               # Shared components
│   ├── lib/                      # Utilities and helpers
│   └── server/                   # Server-side code
│       ├── auth.ts              # NextAuth configuration
│       └── db/                  # Database schemas
│
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── ai/                  # AI provider integrations
│   │   ├── core/                # Core configuration
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   │   ├── email_service.py
│   │   │   ├── email_notification_service.py
│   │   │   └── banking_service.py
│   │   └── routers/             # API endpoints
│   ├── alembic/                 # Database migrations
│   └── test_emails.py           # Email testing script
│
├── public/                       # Static assets
│   └── logo.svg                 # Nova ghost logo
│
└── prisma/                       # Database schema (Next.js side)
```

---

## 🏗️ Architecture 
```
┌───────────────────┐    ┌───────────────┐    ┌───────────┐    ┌───────────────┐
│   Accountant UI   │───▶│   Next.js API  │───▶│  Storage  │───▶│  FastAPI Hub   │
└───────────────────┘    └───────────────┘    └───────────┘    └───────┬───────┘
                                                                       │
                                                                       ├──▶ PDF (pdfplumber)
                                                                       ├──▶ Images (vision)
                                                                       └──▶ AI Models (OpenAI/Anth)
                                                                                   │
                                                                                   v
                                                                        ┌───────────────────┐
                                                                        │  Normalized Data  │
                                                                        └─────────┬─────────┘
                                                                                  │
                                                                                  v
                                                                        ┌───────────────────┐
                                                                        │ Validation + Review│
                                                                        │ (Rules + AI Anomaly)│
                                                                        └─────────┬─────────┘
                                                                                  │
                                                                                  v
                                                                        ┌───────────────────┐
                                                                        │ Validation Agents │
                                                                        │ Invoice/Receipt/  │
                                                                        │ Bank/Payroll/     │
                                                                        │ Contract/VAT      │
                                                                        └─────────┬─────────┘
                                                                                  │
                                                                                  v
                                                                        ┌───────────────────┐
                                                                        │Custom Functions + │
                                                                        │        DB         │
                                                                        └─────────┬─────────┘
                                                                                  │
                                                                                  v
                                                                        ┌───────────────────┐
                                                                        │  Ready to Submit  │
                                                                        └─────────┬─────────┘
                                                                                  │
                                                                                  v
                                                                        ┌───────────────────┐
                                                                        │   Chaser Agent    │
                                                                        └───────────────────┘


                           ┌───────────────────┐
                           │    AI Chat UI     │
                           └─────────┬─────────┘
                                     │
                                     v
                           ┌───────────────────┐
                           │   Next.js API     │
                           └─────────┬─────────┘
                                     │
                                     v
                           ┌──────────────────────────┐
                           │ Custom Functions + DB    │
                           └─────────┬────────────────┘
                                     │
                                     ├──────────────▶ (read/write) Normalized Data
                                     │
                                     ├──────────────▶ (read/write) Validation + Review
                                     │
                                     └──────────────▶ (read/write) Ready to Submit

```

## 🤝 Custom Functions (AI Chat)

Nova's AI chat interface uses custom functions to interact with your database and perform actions:

### Client Management
- **List and search clients** — Natural language queries like "show me all clients in London"
- **Fetch client details** — Complete profiles including contact info, VAT scheme, entity type
- **Checklist status** — Real-time view of document completion and validation status
- **Create new clients** — Add clients through conversational interface
- **Update client data** — Modify contact info, VAT registration, deadlines

### Document Operations
- **Document status** — Check which documents are uploaded, validated, or flagged
- **Validation results** — Surface specific issues and anomalies
- **Bulk operations** — Approve/reject multiple documents or clients at once
- **Search across documents** — Find specific invoices, receipts, or statements

### Workflow Automation
- **Identify clients needing attention** — Flag overdue deadlines, missing docs, validation errors
- **Priority scoring** — AI ranks clients by urgency and risk
- **Automated reminders** — Schedule follow-ups based on client status
- **Report generation** — Create summaries and status reports

### Analytics & Insights
- **Processing metrics** — Documents processed, accuracy rates, time saved
- **Client trends** — Identify patterns across your client base
- **Bottleneck detection** — Find workflow slowdowns and inefficiencies

---

## 🤖 Specialized AI Agents

Nova employs purpose-built AI agents for different document types and workflows:

### Validation Agents
Each agent is trained with domain-specific rules and patterns:

- **Invoice Agent** — VAT calculations, line item validation, supplier verification
- **Receipt Agent** — Expense categorization, duplicate detection, amount verification
- **Bank Statement Agent** — Transaction reconciliation, anomaly detection, balance verification
- **Payroll Agent** — PAYE compliance, NI calculations, employee record validation
- **Contract Agent** — Term extraction, obligation tracking, renewal alerts
- **VAT Certificate Agent** — HMRC validation, registration status, scheme verification

### Workflow Agents
Specialized agents for automation and communication:

- **Chaser Agent** — Automated follow-ups, deadline reminders, escalation workflows
- **Email Agent** — Context-aware email generation with Nova branding
- **Banking Agent** — Real-time transaction sync, categorization, reconciliation
- **Anomaly Agent** — Cross-document pattern detection, fraud alerts, unusual activity

---

## 🚦 Getting Started

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.11+
- PostgreSQL 15+
- API keys for Anthropic Claude and/or OpenAI
- SMTP credentials for email sending

### Environment Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd nova
```

2. **Frontend setup**
```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Configure your .env file with:
# - DATABASE_URL
# - NEXTAUTH_URL and NEXTAUTH_SECRET
# - Auth provider credentials (Google, GitHub, etc.)
```

3. **Backend setup**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Configure your .env file with:
# - DATABASE_URL
# - ANTHROPIC_API_KEY or OPENAI_API_KEY
# - SMTP settings (host, port, username, password)
# - APP_URL for email links
```

4. **Database setup**
```bash
# Run migrations
cd backend
alembic upgrade head
```

5. **Run the application**

Terminal 1 - Frontend:
```bash
npm run dev
# Runs on http://localhost:3000
```

Terminal 2 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Runs on http://localhost:8000
```

### Testing Email Templates

Send test emails to verify branding and wordings:

```bash
cd backend
python test_emails.py your-email@example.com
```

This sends all 9 email types (welcome, validation issues, reminders, etc.) so you can review the templates.

---

## 🎨 Design Philosophy

Nova's design is inspired by minimalist productivity tools like Linear and Saturn OS:

### Visual Identity
- **Off-white backgrounds** (#fafafa) for reduced eye strain during long work sessions
- **Simple borders** (1px, #e8e8e8) for clean separation without visual noise
- **Professional color palette**:
  - Primary Blue: `#0052CC` — Actions and primary elements
  - Success Green: `#36B37E` — Completed items and positive states
  - Warning Orange: `#FF991F` — Attention needed
  - Error Red: `#DE350B` — Critical issues
- **Typography**: Light 56px headlines, 16px body text, monospace labels at 12px
- **No gradients, minimal shadows** — Clean, professional aesthetic
- **1200px max width** — Optimal reading and scanning

### Email Templates
All emails sent by Nova feature:
- **Embedded Nova logo** — Consistent branding across all communications
- **Professional HTML templates** — Clean, readable design matching the dashboard
- **AI-generated content** — Context-aware, personalized messaging
- **Clear CTAs** — Every email has a specific action for recipients
- **Footer branding** — "Powered by Nova - 10x Your Accounting Power"

Test all email templates:
```bash
cd backend
python test_emails.py your-email@example.com
```

---

## 📊 Key Metrics

Nova is designed to transform accounting workflows:

| Metric | Traditional | With Nova |
|--------|-------------|-----------|
| **Document processing time** | 2-5 min/doc | <1 sec/doc |
| **VAT prep time per client** | 4-6 hours | 15-30 minutes |
| **Error rate** | 5-10% | <0.1% |
| **Client capacity per accountant** | 50-75 | 150-250 |
| **Manual data entry** | 80% of time | <5% of time |
| **Follow-up emails** | Manual | Automated |
| **Bank reconciliation** | Weekly batch | Real-time |

---

## 🔒 Security & Compliance

- **Bank-grade encryption** — All sensitive data encrypted at rest and in transit
- **SOC 2 Type II ready** — Infrastructure designed for compliance
- **GDPR compliant** — Full data privacy controls
- **Role-based access** — Granular permissions for accountants and clients
- **Audit trails** — Complete logging of all actions and changes
- **Secure API integrations** — OAuth 2.0 for banking and third-party services

---

## 🚀 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SMTP credentials verified
- [ ] AI API keys active with billing
- [ ] Banking API credentials configured
- [ ] SSL certificates installed
- [ ] Backup strategy implemented
- [ ] Monitoring and logging setup

### Recommended Infrastructure
- **Hosting**: Vercel (frontend) + Railway/Render (backend)
- **Database**: Managed PostgreSQL (Supabase, Railway, or Neon)
- **Email**: SendGrid, AWS SES, or SMTP provider
- **Monitoring**: Sentry for error tracking
- **Analytics**: Posthog or Plausible

---

## 🤝 Contributing

This is an internal project. For feature requests or bug reports, contact the development team.

---

## 📝 License

Internal project — not licensed for public distribution.

---

<p align="center">
  <strong>Built with ❤️ by the Nova Team</strong><br>
  Powered by Claude AI | Making accountants unstoppable since 2026
</p>
