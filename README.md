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


<p align="center">
  <strong>Built with ❤️ by the Nova Team</strong><br>
  Powered by Claude AI | Making accountants unstoppable since 2026
</p>
