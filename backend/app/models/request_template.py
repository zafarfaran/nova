"""Backward compatibility: Re-export from new location."""

from app.models.requests import RequestTemplate, RequestTemplateItem

__all__ = ["RequestTemplate", "RequestTemplateItem"]
