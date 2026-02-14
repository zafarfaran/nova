"""Backward compatibility: Re-export from new location."""

from app.models.validation.validation import ValidationResult, RuleType, ValidationStatus

__all__ = ["ValidationResult", "RuleType", "ValidationStatus"]
