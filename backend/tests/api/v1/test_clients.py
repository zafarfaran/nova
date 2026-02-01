"""Unit tests for Clients API endpoints."""

import uuid
import pytest
from fastapi import status
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.models.clients import Client
from app.schemas.clients import ClientCreate, ClientUpdate, OnboardingCompleteRequest


class TestCreateClient:
    """Tests for POST /api/v1/clients"""

    def test_create_client_success(self, client, db_session, sample_client_data):
        """Test successful client creation."""
        response = client.post("/api/v1/clients", json=sample_client_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_client_data["name"]
        assert data["contact_email"] == sample_client_data["contact_email"]
        assert data["vat_number"] == sample_client_data["vat_number"]
        assert "id" in data
        assert "created_at" in data

    def test_create_client_duplicate_vat_number(self, client, db_session, sample_client_data):
        """Test creating client with duplicate VAT number."""
        # Create first client
        client.post("/api/v1/clients", json=sample_client_data)
        
        # Try to create duplicate
        response = client.post("/api/v1/clients", json=sample_client_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_create_client_missing_required_fields(self, client):
        """Test creating client with missing required fields."""
        response = client.post("/api/v1/clients", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_client_invalid_email(self, client, sample_client_data):
        """Test creating client with invalid email."""
        sample_client_data["contact_email"] = "invalid-email"
        response = client.post("/api/v1/clients", json=sample_client_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListClients:
    """Tests for GET /api/v1/clients"""

    def test_list_clients_empty(self, client, db_session):
        """Test listing clients when none exist."""
        response = client.get("/api/v1/clients")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_clients_with_data(self, client, db_session, sample_client_data):
        """Test listing clients with data."""
        # Create multiple clients
        for i in range(3):
            client_data = sample_client_data.copy()
            unique_id = str(uuid.uuid4())[:8].replace("-", "").upper()
            client_data["contact_email"] = f"test{i}-{unique_id}@example.com"
            client_data["vat_number"] = f"GB{unique_id}"
            client.post("/api/v1/clients", json=client_data)
        
        response = client.get("/api/v1/clients")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_clients_pagination(self, client, db_session, sample_client_data):
        """Test client listing with pagination."""
        # Create 5 clients
        for i in range(5):
            client_data = sample_client_data.copy()
            unique_id = str(uuid.uuid4())[:8].replace("-", "").upper()
            client_data["contact_email"] = f"test{i}-{unique_id}@example.com"
            client_data["vat_number"] = f"GB{unique_id}"
            client.post("/api/v1/clients", json=client_data)
        
        # Test pagination
        response = client.get("/api/v1/clients?skip=2&limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2


class TestGetClient:
    """Tests for GET /api/v1/clients/{client_id}"""

    def test_get_client_success(self, client, db_session, sample_client_data):
        """Test getting a client by ID."""
        # Create client
        create_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = create_response.json()["id"]
        
        # Get client
        response = client.get(f"/api/v1/clients/{client_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == client_id
        assert data["name"] == sample_client_data["name"]

    def test_get_client_not_found(self, client):
        """Test getting non-existent client."""
        response = client.get("/api/v1/clients/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


class TestUpdateClient:
    """Tests for PATCH /api/v1/clients/{client_id}"""

    def test_update_client_success(self, client, db_session, sample_client_data):
        """Test updating a client."""
        # Create client
        create_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = create_response.json()["id"]
        
        # Update client
        update_data = {"name": "Updated Client Name"}
        response = client.patch(f"/api/v1/clients/{client_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Client Name"
        assert data["contact_email"] == sample_client_data["contact_email"]  # Unchanged

    def test_update_client_not_found(self, client):
        """Test updating non-existent client."""
        update_data = {"name": "Updated Name"}
        response = client.patch("/api/v1/clients/99999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_client_partial(self, client, db_session, sample_client_data):
        """Test partial client update."""
        # Create client
        create_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = create_response.json()["id"]
        
        # Update only email
        update_data = {"contact_email": "newemail@example.com"}
        response = client.patch(f"/api/v1/clients/{client_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["contact_email"] == "newemail@example.com"
        assert data["name"] == sample_client_data["name"]  # Unchanged


class TestDeleteClient:
    """Tests for DELETE /api/v1/clients/{client_id}"""

    def test_delete_client_success(self, client, db_session, sample_client_data):
        """Test deleting a client."""
        # Create client
        create_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = create_response.json()["id"]
        
        # Delete client
        response = client.delete(f"/api/v1/clients/{client_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deleted
        get_response = client.get(f"/api/v1/clients/{client_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_client_not_found(self, client):
        """Test deleting non-existent client."""
        response = client.delete("/api/v1/clients/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestOnboardingComplete:
    """Tests for POST /api/v1/clients/{client_id}/onboarding-complete"""

    def test_onboarding_complete_success(self, client, db_session, sample_client_data):
        """Test onboarding completion."""
        # Create client
        create_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = create_response.json()["id"]
        
        # Create engagement
        engagement_data = {
            "client_id": client_id,
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
        }
        engagement_response = client.post("/api/v1/engagements", json=engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        
        # Complete onboarding
        onboarding_data = {
            "client_id": client_id,
            "engagement_id": engagement_id,
            "completed_items": 5,
            "not_applicable_items": 2,
            "total_items": 7,
        }
        response = client.post(
            f"/api/v1/clients/{client_id}/onboarding-complete",
            json=onboarding_data
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["client_id"] == client_id
        assert data["engagement_id"] == engagement_id

    def test_onboarding_complete_client_mismatch(self, client, db_session, sample_client_data):
        """Test onboarding with mismatched client ID."""
        # Create client
        create_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = create_response.json()["id"]
        
        onboarding_data = {
            "client_id": 99999,  # Different ID
            "completed_items": 5,
            "not_applicable_items": 2,
            "total_items": 7,
        }
        response = client.post(
            f"/api/v1/clients/{client_id}/onboarding-complete",
            json=onboarding_data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_onboarding_complete_client_not_found(self, client):
        """Test onboarding for non-existent client."""
        onboarding_data = {
            "client_id": 99999,
            "completed_items": 5,
            "not_applicable_items": 2,
            "total_items": 7,
        }
        response = client.post(
            "/api/v1/clients/99999/onboarding-complete",
            json=onboarding_data
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
