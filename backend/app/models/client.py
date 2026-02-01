"""Backward compatibility: Re-export from new location."""

from app.models.clients import Client, EntityType, ClientType

__all__ = ["Client", "EntityType", "ClientType"]
