"""Student Loan domain module.

Wraps the student loan calculator (Phase 3 stub). Catches
NotImplementedError and returns a placeholder result until the
engine module is fully implemented.
"""

import logging

from app.services.tax.domains.base import BaseTaxDomain
from app.tax.student_loan import calculate_student_loan

logger = logging.getLogger(__name__)


class StudentLoanDomain(BaseTaxDomain):
    """Student Loan calculation domain."""

    @property
    def name(self) -> str:
        return "student_loan"

    @property
    def display_name(self) -> str:
        return "Student Loan"

    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Calculate student loan repayment from client data.

        Expects client_data with:
            gross_income: float
            plan: str (default "plan_2")
        """
        gross_income = float(client_data.get("gross_income", 0))
        plan = client_data.get("plan", "plan_2")

        try:
            result = calculate_student_loan(gross_income, plan=plan)
            return result
        except NotImplementedError:
            logger.info("Student loan engine not yet implemented (Phase 3)")
            return {
                "status": "placeholder",
                "message": "Student loan calculation not yet implemented (Phase 3)",
                "gross_income": gross_income,
                "plan": plan,
            }

    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Return empty observations (stub domain)."""
        return []
