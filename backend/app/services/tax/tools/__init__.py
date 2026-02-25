"""Tool registry — maps tool names to executor functions."""

import logging

from app.services.tax.tools.dashboard import execute_generate_dashboard
from app.services.tax.tools.meeting_notes import execute_search_meeting_notes
from app.services.tax.tools.observations import execute_save_observation
from app.services.tax.tools.tax_engine import (
    execute_compute_tax_position,
    execute_model_salary_sacrifice,
    execute_model_personal_pension,
)

logger = logging.getLogger(__name__)

TOOL_EXECUTORS: dict = {
    "generate_dashboard": execute_generate_dashboard,
    "search_meeting_notes": execute_search_meeting_notes,
    "compute_tax_position": execute_compute_tax_position,
    "model_salary_sacrifice": execute_model_salary_sacrifice,
    "model_personal_pension": execute_model_personal_pension,
    "save_observation": execute_save_observation,
}


def execute_tool(
    name: str, tool_input: dict, context: dict | None = None
) -> dict:
    """Look up and run a tool executor by name."""
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        logger.warning("Unknown tool requested, tool=%s", name)
        return {"error": f"Unknown tool: {name}"}
    return executor(tool_input, context=context)
