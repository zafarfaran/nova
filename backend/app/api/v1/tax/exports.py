"""Export endpoints — generate PDF reports.

Adapted from Helio's exports router (helio/apps/api/app/routers/exports.py).
Changes from Helio original:
  - async -> sync
  - pdf_report import from app.services.tax.pdf_report
  - Tags prefixed with 'tax-'
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.tax.pdf_report import generate_tax_report

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tax-exports"])


class ExportRequest(BaseModel):
    client: dict[str, Any]
    tax_position: dict[str, Any]
    dashboard_data: dict[str, Any]
    scenarios: list[dict[str, Any]] | None = None
    ai_observations: list[dict[str, Any]] | None = None
    meeting_notes: list[dict[str, Any]] | None = None


@router.post("/exports/tax-report")
def export_tax_report(req: ExportRequest) -> StreamingResponse:
    """Generate and return a PDF tax report."""
    client_name = f"{req.client.get('first_name', '')}_{req.client.get('last_name', '')}".strip("_") or "client"
    tax_year = req.tax_position.get("tax_year", "2024-25").replace("/", "-")

    buf = generate_tax_report(
        client=req.client,
        tax_position=req.tax_position,
        dashboard_data=req.dashboard_data,
        scenarios=req.scenarios,
        ai_observations=req.ai_observations,
        meeting_notes=req.meeting_notes,
    )

    filename = f"nova-tax-report-{client_name}-{tax_year}.pdf"

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
