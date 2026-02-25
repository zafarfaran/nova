"""Tax client endpoints — list clients with tax summaries and detail views.

Adapted from Helio's clients router (helio/apps/api/app/routers/clients.py).
Changes from Helio original:
  - async -> sync (Nova uses synchronous SQLAlchemy)
  - AsyncSession -> Session from sqlalchemy.orm
  - get_db_session -> get_db from app.core.database
  - structlog -> stdlib logging
  - Client import from app.models.clients.client
  - TaxProfile, TaxObservation, TaxMeetingNote from app.models.tax
  - Household model removed (Nova has no households table)
  - Household-related endpoints removed (list_households, update_household)
  - Client fields adapted for Nova's schema (name instead of first_name/last_name, etc.)
  - Tags prefixed with 'tax-'
  - client_id is int (Nova) not str (Helio)
"""

import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clients.client import Client
from app.models.tax import TaxMeetingNote, TaxObservation, TaxProfile
from app.tax.engine import compute_full_tax_position
from app.tax.types import IncomeSource as TaxIncomeSource, IncomeType

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tax-clients"])


class IncomeSourceInput(BaseModel):
    type: Literal["employment", "self_employment", "rental", "pension_income", "savings", "dividends", "other"]
    gross_amount: float
    label: str = ""


class ComputeTaxProfileRequest(BaseModel):
    income_sources: list[IncomeSourceInput]
    pension_contributions: float = 0
    gift_aid: float = 0
    claims_child_benefit: bool = False
    number_of_children: int = 0
    isa_contributions: float = 0
    cgt_gains: float = 0

    @field_validator("income_sources")
    @classmethod
    def validate_income_sources(cls, v: list) -> list:
        if len(v) == 0:
            raise ValueError("At least one income source is required")
        return v


@router.get("/clients")
def list_clients(
    session: Session = Depends(get_db),
):
    """List all clients with their latest tax profile summary."""
    logger.info("Listing clients for tax summaries")

    result = session.execute(select(Client))
    clients = list(result.scalars().all())

    clients_out = []
    for client in clients:
        # Fetch latest TaxProfile for each client (by created_at DESC, limit 1)
        tp_result = session.execute(
            select(TaxProfile)
            .where(TaxProfile.client_id == client.id)
            .order_by(desc(TaxProfile.created_at))
            .limit(1)
        )
        tax_profile = tp_result.scalar_one_or_none()

        clients_out.append({
            "id": client.id,
            "name": client.name,
            "contact_email": client.contact_email,
            "entity_type": client.entity_type.value if client.entity_type else None,
            "tax_year": tax_profile.tax_year if tax_profile else None,
            "total_income": tax_profile.total_income if tax_profile else None,
            "total_tax": tax_profile.total_tax if tax_profile else None,
            "effective_rate": tax_profile.effective_rate if tax_profile else None,
            "marginal_rate": tax_profile.marginal_rate if tax_profile else None,
        })

    logger.info("Clients listed, count=%d", len(clients_out))

    return {"clients": clients_out}


@router.get("/clients/{client_id}")
def get_client(
    client_id: int,
    session: Session = Depends(get_db),
):
    """Get client detail with full tax profile and observations."""
    logger.info("Fetching client detail, client_id=%s", client_id)

    # Load client
    result = session.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if client is None:
        logger.warning("Client not found, client_id=%s", client_id)
        raise HTTPException(status_code=404, detail="Client not found")

    # Load latest tax profile
    tp_result = session.execute(
        select(TaxProfile)
        .where(TaxProfile.client_id == client_id)
        .order_by(desc(TaxProfile.created_at))
        .limit(1)
    )
    tax_profile = tp_result.scalar_one_or_none()

    # Load observations
    obs_result = session.execute(
        select(TaxObservation)
        .where(TaxObservation.client_id == client_id)
        .order_by(desc(TaxObservation.created_at))
    )
    observations = list(obs_result.scalars().all())

    # Build tax profile dict with all JSON fields
    tax_profile_out = None
    if tax_profile:
        tax_profile_out = {
            "tax_year": tax_profile.tax_year,
            "total_income": tax_profile.total_income,
            "adjusted_net_income": tax_profile.adjusted_net_income,
            "taxable_income": tax_profile.taxable_income,
            "income_tax": tax_profile.income_tax,
            "national_insurance": tax_profile.national_insurance,
            "dividend_tax": tax_profile.dividend_tax,
            "total_tax": tax_profile.total_tax,
            "effective_rate": tax_profile.effective_rate,
            "marginal_rate": tax_profile.marginal_rate,
            "personal_allowance": tax_profile.personal_allowance,
            "pa_status": tax_profile.pa_status,
            "in_pa_taper_zone": tax_profile.in_pa_taper_zone,
            "hicbc_applies": tax_profile.hicbc_applies,
            "pension_taper_applies": tax_profile.pension_taper_applies,
            "income_sources": tax_profile.income_sources,
            "pension_data": tax_profile.pension_data,
            "allowances": tax_profile.allowances,
            "hicbc": tax_profile.hicbc,
            "tax_breakdown": tax_profile.tax_breakdown,
            "ni_breakdown": tax_profile.ni_breakdown,
        }

    # Build observations list
    observations_out = [
        {
            "id": obs.id,
            "tax_year": obs.tax_year,
            "title": obs.title,
            "description": obs.description,
            "severity": obs.severity,
            "priority": obs.priority,
            "category": obs.category,
            "potential_saving": obs.potential_saving,
            "deadline": obs.deadline,
            "action_required": obs.action_required,
            "is_dismissed": obs.is_dismissed,
            "source": obs.source,
            "created_at": obs.created_at.isoformat() if obs.created_at else None,
        }
        for obs in observations
    ]

    logger.info(
        "Client detail loaded, client_id=%s, has_tax_profile=%s, observation_count=%d",
        client_id,
        tax_profile is not None,
        len(observations_out),
    )

    return {
        "id": client.id,
        "name": client.name,
        "contact_email": client.contact_email,
        "entity_type": client.entity_type.value if client.entity_type else None,
        "country_code": client.country_code,
        "company_number": client.company_number,
        "utr": client.utr,
        "ni_number": client.ni_number,
        "notes": client.notes,
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "tax_profile": tax_profile_out,
        "observations": observations_out,
    }


@router.post("/clients/{client_id}/tax-profile")
def compute_client_tax_profile(
    client_id: int,
    body: ComputeTaxProfileRequest,
    session: Session = Depends(get_db),
):
    """Compute and save a tax profile for a client using the deterministic engine."""

    # Load client
    result = session.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    logger.info(
        "Computing tax profile, client_id=%s, income_sources=%s, pension_contributions=%s, gift_aid=%s",
        client_id,
        [{"type": s.type, "gross_amount": s.gross_amount} for s in body.income_sources],
        body.pension_contributions,
        body.gift_aid,
    )

    # Build engine inputs
    engine_sources = [
        TaxIncomeSource(
            source_type=IncomeType(s.type),
            gross_amount=s.gross_amount,
            label=s.label or s.type.replace("_", " ").title(),
        )
        for s in body.income_sources
    ]

    # Determine region — Nova's Client doesn't have a region field,
    # default to "england"
    region = "england"

    # Run engine
    pos = compute_full_tax_position(
        engine_sources,
        pension_contributions=body.pension_contributions,
        gift_aid=body.gift_aid,
        region=region,
        number_of_children=body.number_of_children,
        claims_child_benefit=body.claims_child_benefit,
        cgt_gains=body.cgt_gains,
    )

    # Delete existing tax profile and observations for this client + tax year
    existing_tp = session.execute(
        select(TaxProfile).where(
            TaxProfile.client_id == client_id,
            TaxProfile.tax_year == pos.tax_year,
        )
    )
    old_tp = existing_tp.scalar_one_or_none()
    if old_tp:
        session.delete(old_tp)

    existing_obs = session.execute(
        select(TaxObservation).where(
            TaxObservation.client_id == client_id,
            TaxObservation.source == "engine",
        )
    )
    for obs in existing_obs.scalars().all():
        session.delete(obs)

    session.flush()

    # Save new TaxProfile
    tax_profile = TaxProfile(
        client_id=client_id,
        tax_year=pos.tax_year,
        total_income=pos.total_income,
        adjusted_net_income=pos.adjusted_net_income,
        taxable_income=pos.taxable_income,
        income_tax=pos.income_tax,
        national_insurance=pos.national_insurance,
        dividend_tax=pos.dividend_tax,
        total_tax=pos.total_tax,
        effective_rate=pos.effective_rate,
        marginal_rate=pos.marginal_rate,
        personal_allowance=pos.personal_allowance,
        pa_status=pos.pa_status,
        in_pa_taper_zone=pos.in_pa_taper_zone,
        hicbc_applies=pos.hicbc_applies,
        pension_taper_applies=pos.pension_taper_applies,
        income_sources=[
            {
                "source_type": s.source_type.value,
                "label": s.label or s.source_type.value.replace("_", " ").title(),
                "gross_amount": s.gross_amount,
            }
            for s in pos.income_sources
        ],
        pension_data={
            "contributions": body.pension_contributions,
            "aa_remaining": pos.pension_aa_result.remaining if pos.pension_aa_result else 60_000 - body.pension_contributions,
            "annual_allowance": pos.pension_aa_result.annual_allowance if pos.pension_aa_result else 60_000,
        },
        allowances=[
            {
                "type": "personal_allowance",
                "label": "Personal Allowance",
                "annual_limit": 12_570,
                "used": min(pos.total_income, pos.personal_allowance),
                "remaining": max(0, pos.personal_allowance - pos.total_income),
                "status": "fully_used" if pos.total_income >= pos.personal_allowance else "available",
            },
            {
                "type": "pension_aa",
                "label": "Pension Annual Allowance",
                "annual_limit": 60_000,
                "used": body.pension_contributions,
                "remaining": pos.pension_aa_result.remaining if pos.pension_aa_result else 60_000 - body.pension_contributions,
            },
            {
                "type": "dividend",
                "label": "Dividend Allowance",
                "annual_limit": 500,
                "used": pos.income_tax_result.dividend_allowance_used,
                "remaining": 500 - pos.income_tax_result.dividend_allowance_used,
            },
            {
                "type": "isa",
                "label": "ISA Allowance",
                "annual_limit": 20_000,
                "used": body.isa_contributions,
                "remaining": 20_000 - body.isa_contributions,
            },
            {
                "type": "cgt_aea",
                "label": "CGT Annual Exemption",
                "annual_limit": 3_000,
                "used": body.cgt_gains,
                "remaining": max(0, 3_000 - body.cgt_gains),
            },
        ],
        hicbc={
            "number_of_children": body.number_of_children,
            "claims_child_benefit": body.claims_child_benefit,
            "child_benefit_amount": pos.hicbc_result.child_benefit_annual if pos.hicbc_result else 0,
            "clawback_percentage": pos.hicbc_result.clawback_percentage if pos.hicbc_result else 0,
            "hicbc_charge": pos.hicbc_result.hicbc_charge if pos.hicbc_result else 0,
        },
        tax_breakdown=[
            {
                "band": b.name,
                "amount": b.income_in_band,
                "rate": b.rate,
                "tax": b.tax,
            }
            for b in pos.income_tax_result.non_savings_bands
        ],
        ni_breakdown={
            "class1": {
                "total_employee_ni": pos.ni_result.class_1.total_employee_ni if pos.ni_result.class_1 else 0,
            },
            "class2": {
                "annual_ni": pos.ni_result.class_2.annual_ni if pos.ni_result.class_2 else 0,
            },
            "class4": {
                "total_ni": pos.ni_result.class_4.total_ni if pos.ni_result.class_4 else 0,
            },
        },
        status="computed",
        data_confidence="high",
    )
    session.add(tax_profile)

    # Save observations
    for obs_item in pos.observations:
        session.add(TaxObservation(
            client_id=client_id,
            tax_year=pos.tax_year,
            title=obs_item.title,
            description=obs_item.description,
            severity=obs_item.severity,
            priority="high" if obs_item.severity in ("warning", "critical") else "medium",
            category=obs_item.category,
            potential_saving=obs_item.potential_saving,
            source="engine",
        ))

    session.flush()

    logger.info("Tax profile computed and saved, client_id=%s, total_tax=%s", client_id, pos.total_tax)

    # Return full client detail (reuse existing endpoint logic)
    return get_client(client_id, session)


class CreateObservationRequest(BaseModel):
    title: str
    description: str
    severity: Literal["info", "warning", "opportunity"]
    category: str
    potential_saving: float | None = None
    source: Literal["engine", "ai"] = "ai"


@router.post("/clients/{client_id}/observations", status_code=201)
def create_observation(
    client_id: int,
    body: CreateObservationRequest,
    session: Session = Depends(get_db),
):
    """Create a single observation for a client."""
    result = session.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    priority = "high" if body.severity == "warning" else ("medium" if body.severity == "opportunity" else "low")

    obs = TaxObservation(
        client_id=client_id,
        title=body.title,
        description=body.description,
        severity=body.severity,
        priority=priority,
        category=body.category,
        potential_saving=body.potential_saving,
        source=body.source,
    )
    session.add(obs)
    session.flush()

    logger.info("Observation created, client_id=%s, observation_id=%s, source=%s", client_id, obs.id, body.source)

    return {
        "id": obs.id,
        "title": obs.title,
        "description": obs.description,
        "severity": obs.severity,
        "priority": priority,
        "category": obs.category,
        "potential_saving": obs.potential_saving,
        "source": obs.source,
    }


@router.delete("/clients/{client_id}/observations/{observation_id}")
def delete_observation(
    client_id: int,
    observation_id: str,
    session: Session = Depends(get_db),
):
    """Delete a single observation by ID."""
    result = session.execute(
        select(TaxObservation)
        .where(TaxObservation.id == observation_id)
        .where(TaxObservation.client_id == client_id)
    )
    obs = result.scalar_one_or_none()
    if obs is None:
        raise HTTPException(status_code=404, detail="Observation not found")

    session.delete(obs)
    session.flush()

    logger.info("Observation deleted, client_id=%s, observation_id=%s", client_id, observation_id)
    return {"success": True}


@router.get("/clients/{client_id}/meeting-notes")
def list_meeting_notes(
    client_id: int,
    session: Session = Depends(get_db),
):
    """List all meeting notes for a client, newest first."""
    # Verify client exists
    result = session.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    # Fetch meeting notes ordered by meeting_date DESC
    notes_result = session.execute(
        select(TaxMeetingNote)
        .where(TaxMeetingNote.client_id == client_id)
        .order_by(desc(TaxMeetingNote.meeting_date))
    )
    notes = list(notes_result.scalars().all())

    logger.info("Meeting notes listed, client_id=%s, count=%d", client_id, len(notes))

    return {
        "meeting_notes": [
            {
                "id": note.id,
                "client_id": note.client_id,
                "meeting_date": note.meeting_date.isoformat() if note.meeting_date else None,
                "subject": note.subject,
                "attendees": note.attendees,
                "summary": note.summary,
                "action_items": note.action_items,
                "tags": note.tags,
                "created_at": note.created_at.isoformat() if note.created_at else None,
            }
            for note in notes
        ]
    }


# ── Pension History (carry-forward) ──────────────────────────────────


class PensionHistoryInput(BaseModel):
    contributions_history: dict[str, dict]


@router.get("/clients/{client_id}/pension-history")
def get_pension_history(
    client_id: int,
    session: Session = Depends(get_db),
):
    """Return prior-year pension contributions for carry forward."""
    result = session.execute(
        select(TaxProfile)
        .where(TaxProfile.client_id == client_id)
        .order_by(desc(TaxProfile.created_at))
        .limit(1)
    )
    tp = result.scalar_one_or_none()

    history = {}
    if tp and tp.pension_data:
        history = tp.pension_data.get("contributions_history", {})

    return {"client_id": client_id, "contributions_history": history}


@router.put("/clients/{client_id}/pension-history")
def update_pension_history(
    client_id: int,
    body: PensionHistoryInput,
    session: Session = Depends(get_db),
):
    """Save prior-year pension contributions for carry forward."""
    result = session.execute(
        select(TaxProfile)
        .where(TaxProfile.client_id == client_id)
        .order_by(desc(TaxProfile.created_at))
        .limit(1)
    )
    tp = result.scalar_one_or_none()
    if tp is None:
        raise HTTPException(status_code=404, detail="No tax profile found for client")

    pension_data = dict(tp.pension_data or {})
    pension_data["contributions_history"] = body.contributions_history
    tp.pension_data = pension_data
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(tp, "pension_data")
    session.flush()

    logger.info("Pension history updated, client_id=%s, years=%s", client_id, list(body.contributions_history.keys()))
    return {"client_id": client_id, "contributions_history": body.contributions_history}
