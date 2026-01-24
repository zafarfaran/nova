"""Pydantic schemas for Validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.validation import RuleType, ValidationStatus


class ValidationResultBase(BaseModel):
    """Base schema for Validation Result."""

    document_id: int
    rule_type: RuleType
    status: ValidationStatus
    message: str | None = None
    details: str | None = None
    field_name: str | None = None
    expected_value: str | None = None
    actual_value: str | None = None


class ValidationResultResponse(ValidationResultBase):
    """Schema for Validation Result response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ValidationResultList(BaseModel):
    """Schema for listing validation results."""

    items: list[ValidationResultResponse]
    total: int


class ValidationSummary(BaseModel):
    """Summary of validation for a VAT period."""

    vat_period_id: int
    total_documents: int
    validated_documents: int
    failed_documents: int
    pending_documents: int
    total_validations: int
    passed_validations: int
    failed_validations: int
    warning_validations: int
    validation_rate: float


class ValidationRunResponse(BaseModel):
    """Response after running validation."""

    document_id: int
    results: list[ValidationResultResponse]
    passed: int
    failed: int
    warnings: int
    skipped: int
