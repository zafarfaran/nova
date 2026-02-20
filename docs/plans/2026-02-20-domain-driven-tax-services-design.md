# Domain-Driven Tax Services Design

**Date:** 2026-02-20
**Status:** Approved

## Goal

Restructure Nova's tax services and API routes into a plugin-based domain architecture where each tax domain (income tax, NI, child benefit, pensions, etc.) is a self-contained module. Adding a new domain = drop in a folder.

## Architecture

### Layers

1. **Tax engine** (`app/tax/`) — pure calculation modules, untouched
2. **Domain modules** (`app/services/tax/domains/<name>/`) — service + routes + schemas per domain
3. **Registry** (`app/services/tax/domains/__init__.py`) — auto-discovers domains, provides aggregation
4. **Shared services** (`app/services/tax/`) — chat, PDF, LLM stay shared, call domains via registry

### Base Domain Interface

```python
class BaseTaxDomain(ABC):
    name: str                    # e.g. "income_tax"
    display_name: str            # e.g. "Income Tax"

    @abstractmethod
    def calculate(self, client_data: dict, tax_year: str) -> dict:
        """Run this domain's calculation."""

    @abstractmethod
    def get_observations(self, result: dict) -> list[dict]:
        """Return planning insights for this domain."""

    @abstractmethod
    def get_router(self) -> APIRouter:
        """Return this domain's API router."""
```

### Domain Folder Structure

```
backend/app/services/tax/domains/
├── __init__.py              # TaxDomainRegistry with auto-discovery
├── base.py                  # BaseTaxDomain ABC
├── income_tax/
│   ├── __init__.py
│   ├── service.py           # IncomeTaxDomain(BaseTaxDomain)
│   ├── routes.py            # APIRouter(tags=["tax-income-tax"])
│   └── schemas.py           # domain-specific Pydantic models
├── national_insurance/
│   ├── service.py
│   ├── routes.py
│   └── schemas.py
├── child_benefit/
│   ├── service.py
│   ├── routes.py
│   └── schemas.py
├── pensions/
│   ├── service.py
│   ├── routes.py
│   └── schemas.py
├── marriage_allowance/
│   ├── service.py
│   ├── routes.py
│   └── schemas.py
├── student_loan/
│   ├── service.py
│   ├── routes.py
│   └── schemas.py
└── capital_gains/           # placeholder for future
    ├── service.py
    └── schemas.py
```

### Registry

```python
class TaxDomainRegistry:
    _domains: dict[str, BaseTaxDomain] = {}

    def __init__(self):
        self._auto_discover()

    def get(self, name: str) -> BaseTaxDomain
    def all(self) -> list[BaseTaxDomain]
    def calculate_all(self, client_data, tax_year) -> dict
    def get_all_observations(self, results) -> list[dict]
    def get_all_routers(self) -> list[APIRouter]
```

### Starting Domains

| Domain folder | Wraps engine module | Description |
|---|---|---|
| `income_tax/` | `app.tax.income_tax` | Personal allowance, tax bands, PAYE |
| `national_insurance/` | `app.tax.national_insurance` | Class 1, 2, 4 NI |
| `child_benefit/` | `app.tax.hicbc` | High Income Child Benefit Charge |
| `pensions/` | `app.tax.personal_pension`, `pension_aa`, `salary_sacrifice` | Pension relief, annual allowance, salary sacrifice |
| `marriage_allowance/` | `app.tax.marriage_allowance` | Spouse allowance transfer |
| `student_loan/` | `app.tax.student_loan` | Student loan repayments |
| `capital_gains/` | (no engine module yet) | Placeholder for future |

### API Endpoint Pattern

Per domain:
- `GET /api/v1/tax/income-tax/{client_id}/calculate`
- `GET /api/v1/tax/income-tax/{client_id}/observations`

Aggregate:
- `GET /api/v1/tax/profile/{client_id}` — runs all domains, returns unified result

### What Changes

- `clients.py` router → split into per-domain routers + aggregate `/profile` endpoint
- `tools/tax_engine.py` → calls registry instead of hardcoding
- `main.py` → auto-registers domain routers from registry
- `chat.py`, `pdf_report.py` → use registry for domain-aware operations

### What Doesn't Change

- `app/tax/` engine modules — untouched
- `app/models/tax/` DB models — untouched
- `app/schemas/tax/` existing schemas — stay, domains add their own
- `llm/` provider layer — untouched

### Scalability

Adding a new tax domain:
1. Create folder `app/services/tax/domains/<name>/`
2. Implement `service.py` with class extending `BaseTaxDomain`
3. Add `routes.py` with FastAPI router
4. Add `schemas.py` with Pydantic models
5. Done — registry auto-discovers it, routes auto-register
