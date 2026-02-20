"""Observation tool — saves AI-generated observations to the client record."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.clients.client import Client
from app.models.tax import TaxObservation

logger = logging.getLogger(__name__)


def execute_save_observation(
    tool_input: dict, context: dict | None = None
) -> dict:
    """Save an AI-generated observation to the database."""
    client_id = context.get("client_id") if context else None
    if not client_id:
        return {"error": "No client context available"}

    title = tool_input.get("title", "")
    description = tool_input.get("description", "")
    severity = tool_input.get("severity", "info")
    category = tool_input.get("category", "planning")
    potential_saving = tool_input.get("potential_saving")

    if not title or not description:
        return {"error": "Title and description are required"}

    session: Session = SessionLocal()
    try:
        # Verify client exists
        result = session.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()
        if not client:
            return {"error": f"Client {client_id} not found"}

        # Check for duplicate (same title + source=ai for this client)
        existing = session.execute(
            select(TaxObservation).where(
                TaxObservation.client_id == client_id,
                TaxObservation.title == title,
                TaxObservation.source == "ai",
            )
        )
        if existing.scalar_one_or_none():
            return {"success": True, "message": "Observation already exists", "duplicate": True}

        priority = "high" if severity == "warning" else ("medium" if severity == "opportunity" else "low")

        obs = TaxObservation(
            client_id=client_id,
            title=title,
            description=description,
            severity=severity,
            priority=priority,
            category=category,
            potential_saving=potential_saving,
            source="ai",
        )
        session.add(obs)
        session.commit()

        logger.info(
            "AI observation saved, client_id=%s, title=%s, severity=%s, observation_id=%s",
            client_id,
            title,
            severity,
            obs.id,
        )

        return {
            "success": True,
            "observation_id": obs.id,
            "message": f"Observation '{title}' saved to client record.",
        }
    finally:
        session.close()
