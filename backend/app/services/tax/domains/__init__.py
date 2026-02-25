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


_registry: TaxDomainRegistry | None = None


def get_registry() -> TaxDomainRegistry:
    """Get or create the singleton registry."""
    global _registry
    if _registry is None:
        _registry = TaxDomainRegistry()
    return _registry
