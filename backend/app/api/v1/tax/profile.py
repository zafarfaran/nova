"""Aggregate tax profile endpoint — runs all domains for a client."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clients.client import Client
from app.services.tax.domains import get_registry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tax-profile"])


class TaxProfileRequest(BaseModel):
    income_sources: list[dict]
    pension_contributions: float = 0
    employer_contributions: float = 0
    gift_aid: float = 0
    region: str = "england"
    number_of_children: int = 0
    claims_child_benefit: bool = False
    cgt_gains: float = 0
    isa_contributions: float = 0
    tax_year: str = "2025/26"

    @field_validator("income_sources")
    @classmethod
    def validate_income_sources(cls, v):
        if len(v) == 0:
            raise ValueError("At least one income source is required")
        return v


@router.post("/profile/{client_id}")
def compute_full_profile(
    client_id: int,
    body: TaxProfileRequest,
    session: Session = Depends(get_db),
):
    """Run all tax domain calculations for a client and return unified result."""
    result = session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    registry = get_registry()
    client_data = body.model_dump()

    # Run all domains
    results = registry.calculate_all(client_data, body.tax_year)
    observations = registry.get_all_observations(results)

    # Clean internal objects from results
    for domain_result in results.values():
        if isinstance(domain_result, dict):
            for key in list(domain_result.keys()):
                if key.startswith("_"):
                    del domain_result[key]

    return {
        "client_id": client_id,
        "tax_year": body.tax_year,
        "domains": results,
        "observations": observations,
        "available_domains": registry.names(),
    }


@router.get("/domains")
def list_domains():
    """List all registered tax domains."""
    registry = get_registry()
    return {
        "domains": [
            {"name": d.name, "display_name": d.display_name}
            for d in registry.all()
        ]
    }
