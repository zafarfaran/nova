"""API routes for the national_insurance domain."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clients.client import Client
from app.services.tax.domains.national_insurance.schemas import NIRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/clients/{client_id}/calculate")
def calculate_national_insurance(
    client_id: int,
    request: NIRequest,
    session: Session = Depends(get_db),
):
    """Calculate national insurance for a client."""
    # Validate client exists
    result = session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    from app.services.tax.domains.national_insurance.service import NationalInsuranceDomain

    domain = NationalInsuranceDomain()
    client_data = request.model_dump()
    client_data["income_sources"] = [s.model_dump() for s in request.income_sources]

    calculation = domain.calculate(client_data, tax_year=request.tax_year)

    # Strip internal keys (prefixed with _)
    return {k: v for k, v in calculation.items() if not k.startswith("_")}
