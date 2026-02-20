"""Master dashboard schema."""

from pydantic import BaseModel

from app.schemas.tax.allowances import AllowancesTracker
from app.schemas.tax.client import ClientInfo
from app.schemas.tax.observations import Observation
from app.schemas.tax.scenarios import Scenario
from app.schemas.tax.tax import AdjustedNetIncome, IncomeSummary, TaxCalculation


class RelevantTaxData(BaseModel):
    """Master response schema sent to the frontend."""

    client: ClientInfo
    income: IncomeSummary
    tax: TaxCalculation
    adjusted_net_income: AdjustedNetIncome
    allowances: AllowancesTracker
    observations: list[Observation] = []
    scenarios: list[Scenario] = []
