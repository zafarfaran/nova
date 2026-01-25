<p align="center">
  <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNm5qY2VjenM5MnZwZHI4cmd3MTFia2tybnZsMjk2cGxtZHN2anhzdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TbXVwz9MDnwYst8GXj/giphy.gif" alt="Nova GIF" />
</p>

# Nova — Tax Document Helper for Accountants

Nova helps accountants collect, review, and approve tax documents in one place. It combines AI‑assisted extraction with human review so teams can move clients to “Ready to submit” without juggling spreadsheets.

## Highlights
- Multimodal extraction across PDFs and images.
- Review queue with document‑level approve/reject.
- Final review step to mark a client ready to submit.
- AI chat that can find clients and surface their document status.

## Novel Approaches
- **Dual validation loop**: rules + AI anomaly checks, resolved through human approval.
- **Multimodal blending**: PDF structure and vision extraction normalized into one schema.
- **Document‑level resolution**: reduce review fatigue by approving all issues at once.
- **Flow‑aware UX**: client stage changes reflect validation and review state.

## Architecture 
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

## Custom Functions (AI Chat)
- List and search clients
- Fetch client details + checklist status
- Identify clients needing attention
- Create clients and update checklist items

## Specialized Agents
Nova uses different agents for document verification and follow‑up:
- **Invoice Agent**
- **Receipt Agent**
- **Bank Statement Agent**
- **Payroll Agent**
- **Contract Agent**
- **VAT Certificate Agent**
- **Chaser Agent** (automated follow‑ups and reminders)

## License
Internal project — not licensed for public distribution.
