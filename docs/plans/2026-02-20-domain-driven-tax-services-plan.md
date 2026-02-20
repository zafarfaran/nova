# Domain-Driven Tax Services Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure tax services into a plugin-based domain architecture where each tax domain is a self-contained module with auto-discovery.

**Architecture:** A `BaseTaxDomain` ABC defines the interface. Each domain folder contains `service.py`, `routes.py`, `schemas.py`. A `TaxDomainRegistry` auto-discovers domains at startup. The existing tax engine (`app/tax/`) stays untouched — domains wrap it. The monolithic `clients.py` router is archived and replaced by per-domain routers + an aggregate `/profile` endpoint.

**Tech Stack:** FastAPI, SQLAlchemy (sync), Pydantic, existing `app.tax` engine modules

---

## Task 1: Create BaseTaxDomain ABC and Registry

**Files:**
- Create: `backend/app/services/tax/domains/__init__.py`
- Create: `backend/app/services/tax/domains/base.py`

**Step 1: Create the base class**

Create `backend/app/services/tax/domains/base.py`:

```python
"""Base class for all tax domain modules."""

from abc import ABC, abstractmethod

from fastapi import APIRouter


class BaseTaxDomain(ABC):
    """Every tax domain must implement this interface.

    To add a new domain:
    1. Create a folder under domains/ (e.g. domains/capital_gains/)
    2. Create service.py with a class that extends BaseTaxDomain
    3. Implement calculate(), get_observations(), get_router()
    4. The registry auto-discovers it — no other files need changing.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Machine name, e.g. 'income_tax'. Used as URL slug (hyphens auto-added)."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human name, e.g. 'Income Tax'. Used in UI/reports."""

    @abstractmethod
    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Run this domain's calculation. Returns domain-specific result dict."""

    @abstractmethod
    def get_observations(self, calculation_result: dict) -> list[dict]:
        """Extract planning observations from this domain's calculation result."""

    def get_router(self) -> APIRouter | None:
        """Return this domain's API router, or None if no custom endpoints."""
        return None
```

**Step 2: Create the registry with auto-discovery**

Create `backend/app/services/tax/domains/__init__.py`:

```python
"""Tax domain registry — auto-discovers all domain modules."""

import importlib
import logging
import pkgutil
from pathlib import Path

from app.services.tax.domains.base import BaseTaxDomain

logger = logging.getLogger(__name__)


class TaxDomainRegistry:
    """Discovers and registers all tax domain modules."""

    def __init__(self):
        self._domains: dict[str, BaseTaxDomain] = {}
        self._auto_discover()

    def _auto_discover(self):
        """Scan subpackages for classes that extend BaseTaxDomain."""
        domains_dir = Path(__file__).parent
        for importer, modname, ispkg in pkgutil.iter_modules([str(domains_dir)]):
            if not ispkg or modname == "base":
                continue
            try:
                mod = importlib.import_module(f"app.services.tax.domains.{modname}.service")
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseTaxDomain)
                        and attr is not BaseTaxDomain
                    ):
                        instance = attr()
                        self._domains[instance.name] = instance
                        logger.info("Registered tax domain: %s", instance.name)
            except Exception:
                logger.exception("Failed to load tax domain: %s", modname)

    def get(self, name: str) -> BaseTaxDomain:
        """Get a domain by name. Raises KeyError if not found."""
        return self._domains[name]

    def all(self) -> list[BaseTaxDomain]:
        """Return all registered domains."""
        return list(self._domains.values())

    def names(self) -> list[str]:
        """Return all registered domain names."""
        return list(self._domains.keys())

    def calculate_all(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Run all domain calculations, return {domain_name: result}."""
        results = {}
        for name, domain in self._domains.items():
            try:
                results[name] = domain.calculate(client_data, tax_year)
            except Exception:
                logger.exception("Domain calculation failed: %s", name)
                results[name] = {"error": f"{name} calculation failed"}
        return results

    def get_all_observations(self, results: dict) -> list[dict]:
        """Collect observations from all domains given their results."""
        observations = []
        for name, domain in self._domains.items():
            if name in results and "error" not in results[name]:
                try:
                    obs = domain.get_observations(results[name])
                    observations.extend(obs)
                except Exception:
                    logger.exception("Observations failed: %s", name)
        return observations

    def get_all_routers(self) -> list[tuple[str, "APIRouter"]]:
        """Return (url_prefix, router) for all domains that have routes."""
        routers = []
        for domain in self._domains.values():
            router = domain.get_router()
            if router:
                slug = domain.name.replace("_", "-")
                routers.append((slug, router))
        return routers


# Module-level singleton
_registry: TaxDomainRegistry | None = None


def get_registry() -> TaxDomainRegistry:
    """Get or create the singleton registry."""
    global _registry
    if _registry is None:
        _registry = TaxDomainRegistry()
    return _registry
```

**Step 3: Commit**

```bash
git add backend/app/services/tax/domains/
git commit -m "feat: add BaseTaxDomain ABC and auto-discovery registry"
```

---

## Task 2: Create income_tax domain

The first and largest domain. Wraps `app.tax.income_tax` and `app.tax.ani`.

**Files:**
- Create: `backend/app/services/tax/domains/income_tax/__init__.py`
- Create: `backend/app/services/tax/domains/income_tax/service.py`
- Create: `backend/app/services/tax/domains/income_tax/routes.py`
- Create: `backend/app/services/tax/domains/income_tax/schemas.py`

**Step 1: Create schemas**

`backend/app/services/tax/domains/income_tax/schemas.py`:

```python
"""Income tax domain schemas."""

from typing import Literal

from pydantic import BaseModel


class IncomeSourceInput(BaseModel):
    type: Literal["employment", "self_employment", "rental", "pension_income", "savings", "dividends", "other"]
    gross_amount: float
    label: str = ""


class IncomeTaxRequest(BaseModel):
    income_sources: list[IncomeSourceInput]
    pension_contributions: float = 0
    gift_aid: float = 0
    region: str = "england"
    tax_year: str = "2025/26"
```

**Step 2: Create service**

`backend/app/services/tax/domains/income_tax/service.py`:

```python
"""Income tax domain — personal allowance, tax bands, PAYE."""

import logging

from fastapi import APIRouter

from app.services.tax.domains.base import BaseTaxDomain
from app.tax.ani import calculate_adjusted_net_income
from app.tax.income_tax import calculate_income_tax
from app.tax.types import IncomeSource, IncomeType, NON_SAVINGS_TYPES

logger = logging.getLogger(__name__)


class IncomeTaxDomain(BaseTaxDomain):

    @property
    def name(self) -> str:
        return "income_tax"

    @property
    def display_name(self) -> str:
        return "Income Tax"

    def calculate(self, client_data: dict, tax_year: str = "2025/26") -> dict:
        """Calculate income tax from client_data dict."""
        raw_sources = client_data.get("income_sources", [])
        income_sources = [
            IncomeSource(
                source_type=IncomeType(s["type"]),
                gross_amount=float(s["gross_amount"]),
                label=s.get("label", ""),
            )
            for s in raw_sources
        ]

        non_savings = sum(s.net_amount for s in income_sources if s.source_type in NON_SAVINGS_TYPES)
        savings = sum(s.net_amount for s in income_sources if s.source_type == IncomeType.SAVINGS)
        dividends = sum(s.net_amount for s in income_sources if s.source_type == IncomeType.DIVIDENDS)
        total_income = non_savings + savings + dividends

        pension_contributions = float(client_data.get("pension_contributions", 0))
        gift_aid = float(client_data.get("gift_aid", 0))
        region = client_data.get("region", "england")

        ani_result = calculate_adjusted_net_income(
            total_income,
            pension_contributions=pension_contributions,
            gift_aid=gift_aid,
            tax_year=tax_year,
        )

        it_result = calculate_income_tax(
            non_savings_income=non_savings,
            savings_income=savings,
            dividend_income=dividends,
            personal_allowance=ani_result.personal_allowance,
            is_scottish=region.lower() == "scotland",
            gift_aid=gift_aid,
            pension_contributions=pension_contributions,
            tax_year=tax_year,
        )

        return {
            "total_income": total_income,
            "adjusted_net_income": ani_result.adjusted_net_income,
            "personal_allowance": ani_result.personal_allowance,
            "pa_status": str(ani_result.pa_status),
            "in_pa_taper_zone": ani_result.in_taper_zone,
            "taxable_income": it_result.taxable_income,
            "total_income_tax": it_result.total_income_tax,
            "dividend_tax": it_result.dividend_tax,
            "effective_rate": round((it_result.total_income_tax / total_income * 100) if total_income > 0 else 0, 2),
            "bands": [
                {"name": b.name, "income_in_band": b.income_in_band, "rate": b.rate, "tax": b.tax}
                for b in it_result.non_savings_bands
            ],
            "savings_bands": [
                {"name": b.name, "income_in_band": b.income_in_band, "rate": b.rate, "tax": b.tax}
                for b in it_result.savings_bands
            ],
            "dividend_bands": [
                {"name": b.name, "income_in_band": b.income_in_band, "rate": b.rate, "tax": b.tax}
                for b in it_result.dividend_bands
            ],
            "dividend_allowance_used": it_result.dividend_allowance_used,
            "_ani_result": ani_result,
            "_it_result": it_result,
        }

    def get_observations(self, result: dict) -> list[dict]:
        """Income tax observations (PA taper, 60% trap, etc.)."""
        observations = []
        if result.get("in_pa_taper_zone"):
            observations.append({
                "domain": self.name,
                "severity": "warning",
                "title": "Personal Allowance Taper",
                "description": "Income is in the PA taper zone (£100k-£125,140). "
                               "Effective marginal rate is 60%. Consider pension contributions to reduce ANI.",
                "category": "personal_allowance",
            })
        return observations

    def get_router(self) -> APIRouter:
        from app.services.tax.domains.income_tax.routes import router
        return router
```

**Step 3: Create routes**

`backend/app/services/tax/domains/income_tax/routes.py`:

```python
"""Income tax API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clients.client import Client
from app.services.tax.domains.income_tax.schemas import IncomeTaxRequest
from app.services.tax.domains.income_tax.service import IncomeTaxDomain

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tax-income-tax"])
domain = IncomeTaxDomain()


@router.post("/clients/{client_id}/calculate")
def calculate_income_tax(
    client_id: int,
    body: IncomeTaxRequest,
    session: Session = Depends(get_db),
):
    """Calculate income tax for a client."""
    result = session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    client_data = {
        "income_sources": [s.model_dump() for s in body.income_sources],
        "pension_contributions": body.pension_contributions,
        "gift_aid": body.gift_aid,
        "region": body.region,
    }

    calc_result = domain.calculate(client_data, body.tax_year)
    # Remove internal objects before returning
    calc_result.pop("_ani_result", None)
    calc_result.pop("_it_result", None)

    return {"domain": "income_tax", "client_id": client_id, **calc_result}
```

**Step 4: Create `__init__.py`**

`backend/app/services/tax/domains/income_tax/__init__.py`: empty file.

**Step 5: Commit**

```bash
git add backend/app/services/tax/domains/income_tax/
git commit -m "feat: add income_tax domain module"
```

---

## Task 3: Create national_insurance domain

Wraps `app.tax.national_insurance`.

**Files:**
- Create: `backend/app/services/tax/domains/national_insurance/__init__.py`
- Create: `backend/app/services/tax/domains/national_insurance/service.py`
- Create: `backend/app/services/tax/domains/national_insurance/routes.py`
- Create: `backend/app/services/tax/domains/national_insurance/schemas.py`

The service calls `calculate_class_1_ni`, `calculate_class_2_ni`, `calculate_class_4_ni` from `app.tax.national_insurance`. It takes income sources and determines which NI classes apply (employment → Class 1, self-employment → Class 2 + 4).

Schema: same `IncomeSourceInput` plus `region`.
Routes: `POST /clients/{client_id}/calculate` — returns NI breakdown.

Follow the same pattern as Task 2. The `get_observations` method should flag when someone is near the UEL threshold.

**Step 1: Create all 4 files following income_tax pattern**
**Step 2: Commit**

```bash
git add backend/app/services/tax/domains/national_insurance/
git commit -m "feat: add national_insurance domain module"
```

---

## Task 4: Create child_benefit domain

Wraps `app.tax.hicbc`.

**Files:**
- Create: `backend/app/services/tax/domains/child_benefit/__init__.py`
- Create: `backend/app/services/tax/domains/child_benefit/service.py`
- Create: `backend/app/services/tax/domains/child_benefit/routes.py`
- Create: `backend/app/services/tax/domains/child_benefit/schemas.py`

Schema needs: `adjusted_net_income` (or income_sources to compute it), `number_of_children`, `claims_child_benefit`.
Service calls `calculate_hicbc` from `app.tax.hicbc`.
Observations: flag when HICBC applies, show net benefit vs giving up.

**Step 1: Create all 4 files following income_tax pattern**
**Step 2: Commit**

```bash
git add backend/app/services/tax/domains/child_benefit/
git commit -m "feat: add child_benefit domain module"
```

---

## Task 5: Create pensions domain

Wraps `app.tax.personal_pension`, `app.tax.pension_aa`, `app.tax.salary_sacrifice`.

**Files:**
- Create: `backend/app/services/tax/domains/pensions/__init__.py`
- Create: `backend/app/services/tax/domains/pensions/service.py`
- Create: `backend/app/services/tax/domains/pensions/routes.py`
- Create: `backend/app/services/tax/domains/pensions/schemas.py`

This is the most complex domain — it wraps three engine modules.

Schema needs: `income_sources`, `pension_contributions`, `employer_contributions`, `salary_sacrifice_amount`, `pension_contributions_by_year` (for carry-forward).

Service has three calculation modes:
1. `calculate()` — overall pension position (AA, carry-forward)
2. Personal pension scenario (calls `analyse_personal_pension`)
3. Salary sacrifice scenario (calls `analyse_salary_sacrifice`)

Routes:
- `POST /clients/{client_id}/calculate` — pension allowance position
- `POST /clients/{client_id}/model-personal-pension` — scenario modelling
- `POST /clients/{client_id}/model-salary-sacrifice` — scenario modelling
- `GET /clients/{client_id}/pension-history` — carry-forward data (move from current clients.py)
- `PUT /clients/{client_id}/pension-history` — update carry-forward (move from current clients.py)

**Step 1: Create all 4 files**
**Step 2: Commit**

```bash
git add backend/app/services/tax/domains/pensions/
git commit -m "feat: add pensions domain module"
```

---

## Task 6: Create marriage_allowance domain

Wraps `app.tax.marriage_allowance`. Lightweight domain.

**Files:**
- Create: `backend/app/services/tax/domains/marriage_allowance/__init__.py`
- Create: `backend/app/services/tax/domains/marriage_allowance/service.py`
- Create: `backend/app/services/tax/domains/marriage_allowance/schemas.py`

No custom routes needed (calculation only). `get_router()` returns `None`.

**Step 1: Create files**
**Step 2: Commit**

```bash
git add backend/app/services/tax/domains/marriage_allowance/
git commit -m "feat: add marriage_allowance domain module"
```

---

## Task 7: Create student_loan domain

Wraps `app.tax.student_loan`. Lightweight domain.

**Files:**
- Create: `backend/app/services/tax/domains/student_loan/__init__.py`
- Create: `backend/app/services/tax/domains/student_loan/service.py`
- Create: `backend/app/services/tax/domains/student_loan/schemas.py`

No custom routes needed. `get_router()` returns `None`.

**Step 1: Create files**
**Step 2: Commit**

```bash
git add backend/app/services/tax/domains/student_loan/
git commit -m "feat: add student_loan domain module"
```

---

## Task 8: Create capital_gains placeholder domain

No engine module yet — this is a placeholder for future expansion, demonstrating the pattern.

**Files:**
- Create: `backend/app/services/tax/domains/capital_gains/__init__.py`
- Create: `backend/app/services/tax/domains/capital_gains/service.py`
- Create: `backend/app/services/tax/domains/capital_gains/schemas.py`

Service: `calculate()` returns a stub with CGT allowance info. `get_observations()` returns empty list.

**Step 1: Create files**
**Step 2: Commit**

```bash
git add backend/app/services/tax/domains/capital_gains/
git commit -m "feat: add capital_gains placeholder domain"
```

---

## Task 9: Create aggregate profile router

Replace the monolithic `clients.py` with a slim aggregate endpoint that uses the registry.

**Files:**
- Create: `backend/app/api/v1/tax/profile.py`
- Modify: `backend/app/api/v1/tax/__init__.py`

**Step 1: Create the aggregate profile router**

`backend/app/api/v1/tax/profile.py`:

```python
"""Aggregate tax profile endpoint — runs all domains for a client."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.clients.client import Client
from app.models.tax import TaxObservation, TaxProfile
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
    """Run all tax domain calculations for a client and save results."""
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
```

**Step 2: Update `__init__.py` to export**

Update `backend/app/api/v1/tax/__init__.py` to add the profile router.

**Step 3: Commit**

```bash
git add backend/app/api/v1/tax/profile.py backend/app/api/v1/tax/__init__.py
git commit -m "feat: add aggregate tax profile endpoint using domain registry"
```

---

## Task 10: Wire domain routers into main.py

Replace manual router registration with registry auto-discovery.

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/v1/tax/__init__.py`

**Step 1: Update main.py**

Replace the 4 manual tax router lines with:

```python
from app.services.tax.domains import get_registry
from app.api.v1.tax import tax_chat_router, tax_context_router, tax_exports_router, tax_profile_router

# Tax domain routes (auto-discovered)
registry = get_registry()
for slug, domain_router in registry.get_all_routers():
    app.include_router(domain_router, prefix=f"/api/v1/tax/{slug}")

# Shared tax routes
app.include_router(tax_chat_router, prefix="/api/v1/tax")
app.include_router(tax_context_router, prefix="/api/v1/tax")
app.include_router(tax_exports_router, prefix="/api/v1/tax")
app.include_router(tax_profile_router, prefix="/api/v1/tax")
```

**Step 2: Archive the old monolithic clients.py router**

```bash
mv backend/app/api/v1/tax/clients.py _archive/backend/tax_clients_router_monolithic.py
```

**Step 3: Update `__init__.py`**

Remove `tax_clients_router` export, add `tax_profile_router`.

**Step 4: Commit**

```bash
git add backend/app/main.py backend/app/api/v1/tax/ _archive/backend/
git commit -m "feat: wire domain routers via registry, archive monolithic clients router"
```

---

## Task 11: Update tools/tax_engine.py to use registry

Refactor the LLM tool to use the registry so the AI can call domain-specific calculations.

**Files:**
- Modify: `backend/app/services/tax/tools/tax_engine.py`

**Step 1: Update execute_compute_tax_position**

The main `execute_compute_tax_position` function should use `registry.calculate_all()` to get per-domain results, then aggregate them. Keep the `_position_to_summary` and `_position_to_dashboard` functions since they format for the LLM/frontend, but they should now also include domain breakdown data.

Keep `execute_model_salary_sacrifice` and `execute_model_personal_pension` — they can call the pensions domain directly via `registry.get("pensions")`.

**Step 2: Commit**

```bash
git add backend/app/services/tax/tools/tax_engine.py
git commit -m "refactor: tax engine tool uses domain registry"
```

---

## Task 12: Update shared services to use registry

Update chat and PDF report services to be domain-aware.

**Files:**
- Modify: `backend/app/services/tax/system_prompt.py` — include registered domain names in the prompt
- Modify: `backend/app/services/tax/chat.py` — if it references domain-specific logic, route through registry

**Step 1: Update system_prompt.py**

Add available domains list to the system prompt so the LLM knows what domains are available.

**Step 2: Update chat.py if needed**

Only modify if it hardcodes domain-specific logic. If it already delegates to tools, no changes needed.

**Step 3: Commit**

```bash
git add backend/app/services/tax/system_prompt.py backend/app/services/tax/chat.py
git commit -m "refactor: shared tax services use domain registry"
```

---

## Task 13: Verify and final commit

**Step 1: Verify auto-discovery works**

```bash
cd backend && python3 -c "
from app.services.tax.domains import get_registry
r = get_registry()
print('Registered domains:', r.names())
print('Routers:', [(s, r) for s, r in r.get_all_routers()])
"
```

Expected: `['income_tax', 'national_insurance', 'child_benefit', 'pensions', 'marriage_allowance', 'student_loan', 'capital_gains']`

**Step 2: Verify no broken imports**

```bash
cd backend && python3 -c "from app.main import app; print('App loaded OK')"
```

**Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: resolve any remaining integration issues"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | BaseTaxDomain ABC + TaxDomainRegistry with auto-discovery |
| 2 | income_tax domain (wraps income_tax + ani engine) |
| 3 | national_insurance domain (wraps NI engine) |
| 4 | child_benefit domain (wraps hicbc engine) |
| 5 | pensions domain (wraps pension + salary sacrifice engine) |
| 6 | marriage_allowance domain (lightweight, no routes) |
| 7 | student_loan domain (lightweight, no routes) |
| 8 | capital_gains placeholder domain |
| 9 | Aggregate profile router using registry |
| 10 | Wire domain routers into main.py, archive old clients.py |
| 11 | Update tools/tax_engine.py to use registry |
| 12 | Update shared services (system_prompt, chat) |
| 13 | Verify full integration |
