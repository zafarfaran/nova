"""API routes for the pensions domain.

Provides three endpoints:
  - POST /clients/{client_id}/calculate          — pension AA position
  - POST /clients/{client_id}/model-personal-pension — personal pension modelling
  - POST /clients/{client_id}/model-salary-sacrifice — salary sacrifice modelling
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clients.client import Client
from app.services.tax.domains.pensions.schemas import (
    PensionAARequest,
    PersonalPensionRequest,
    SalarySacrificeRequest,
)
from app.tax.personal_pension import analyse_personal_pension
from app.tax.salary_sacrifice import analyse_salary_sacrifice
from app.tax.types import IncomeSource, IncomeType

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_client(client_id: int, session: Session) -> None:
    """Validate that the client exists, raise 404 if not."""
    result = session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")


def _parse_income_sources(raw_sources: list[dict]) -> list[IncomeSource]:
    """Convert raw dicts to IncomeSource objects."""
    return [
        IncomeSource(
            source_type=IncomeType(s["type"]),
            gross_amount=float(s["gross_amount"]),
            label=s.get("label", ""),
        )
        for s in raw_sources
    ]


@router.post("/clients/{client_id}/calculate")
def calculate_pension_aa(
    client_id: int,
    request: PensionAARequest,
    session: Session = Depends(get_db),
):
    """Calculate pension annual allowance position for a client."""
    _validate_client(client_id, session)

    from app.services.tax.domains.pensions.service import PensionsDomain

    domain = PensionsDomain()
    client_data = request.model_dump()
    client_data["income_sources"] = [s.model_dump() for s in request.income_sources]

    calculation = domain.calculate(client_data, tax_year=request.tax_year)

    # Strip internal keys (prefixed with _)
    return {k: v for k, v in calculation.items() if not k.startswith("_")}


@router.post("/clients/{client_id}/model-personal-pension")
def model_personal_pension(
    client_id: int,
    request: PersonalPensionRequest,
    session: Session = Depends(get_db),
):
    """Model personal pension contribution scenarios for a client."""
    _validate_client(client_id, session)

    income_sources = _parse_income_sources(
        [s.model_dump() for s in request.income_sources]
    )

    analysis, _tax_position = analyse_personal_pension(
        income_sources=income_sources,
        proposed_contribution=request.proposed_contribution,
        current_contribution=request.current_contribution,
        employer_contributions=request.employer_contributions,
        gift_aid=request.gift_aid,
        region=request.region,
        number_of_children=request.number_of_children,
        claims_child_benefit=request.claims_child_benefit,
        pension_contributions_by_year=request.contributions_by_year,
    )

    return analysis


@router.post("/clients/{client_id}/model-salary-sacrifice")
def model_salary_sacrifice(
    client_id: int,
    request: SalarySacrificeRequest,
    session: Session = Depends(get_db),
):
    """Model salary sacrifice scenarios for a client."""
    _validate_client(client_id, session)

    other_sources = None
    if request.other_income_sources:
        other_sources = _parse_income_sources(
            [s.model_dump() for s in request.other_income_sources]
        )

    analysis, _tax_position = analyse_salary_sacrifice(
        gross_salary=request.gross_salary,
        sacrifice_amount=request.sacrifice_amount,
        current_sacrifice=request.current_sacrifice,
        other_income_sources=other_sources,
        region=request.region,
        number_of_children=request.number_of_children,
        claims_child_benefit=request.claims_child_benefit,
        pension_contributions_by_year=request.contributions_by_year,
    )

    return analysis
