"""Pydantic schemas for the student_loan domain."""

from typing import Literal

from pydantic import BaseModel


class StudentLoanRequest(BaseModel):
    gross_income: float
    plan: Literal["plan_1", "plan_2", "plan_4", "plan_5", "postgraduate"] = "plan_2"
