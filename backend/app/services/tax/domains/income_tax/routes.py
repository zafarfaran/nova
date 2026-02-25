"""API routes for the income_tax domain."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clients.client import Client
from app.services.tax.domains.income_tax.schemas import IncomeTaxRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tax-income-tax"])


@router.post("/clients/{client_id}/calculate")
def calculate_income_tax(
    client_id: int,
    request: IncomeTaxRequest,
    session: Session = Depends(get_db),
):
    """Calculate income tax for a client."""
    # Validate client exists
    result = session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    from app.services.tax.domains.income_tax.service import IncomeTaxDomain

    domain = IncomeTaxDomain()
    client_data = request.model_dump()
    # Convert IncomeSourceInput models to dicts
    client_data["income_sources"] = [s.model_dump() for s in request.income_sources]

    calculation = domain.calculate(client_data, tax_year=request.tax_year)

    # Strip internal keys (prefixed with _)
    return {k: v for k, v in calculation.items() if not k.startswith("_")}
