"""API routes for the child_benefit domain."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clients.client import Client
from app.services.tax.domains.child_benefit.schemas import ChildBenefitRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/clients/{client_id}/calculate")
def calculate_child_benefit(
    client_id: int,
    request: ChildBenefitRequest,
    session: Session = Depends(get_db),
):
    """Calculate child benefit / HICBC for a client."""
    # Validate client exists
    result = session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    from app.services.tax.domains.child_benefit.service import ChildBenefitDomain

    domain = ChildBenefitDomain()
    client_data = request.model_dump()

    calculation = domain.calculate(client_data, tax_year=request.tax_year)

    # Strip internal keys (prefixed with _)
    return {k: v for k, v in calculation.items() if not k.startswith("_")}
