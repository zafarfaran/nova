"""Unit tests for Engagements API endpoints."""

import pytest
from fastapi import status


class TestCreateEngagement:
    """Tests for POST /api/v1/engagements"""

    def test_create_engagement_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test successful engagement creation."""
        # Create client first
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        
        response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["client_id"] == client_id
        assert "id" in data
        assert "created_at" in data

    def test_create_engagement_client_not_found(self, client, sample_engagement_data):
        """Test creating engagement for non-existent client."""
        sample_engagement_data["client_id"] = 99999
        response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "client not found" in response.json()["detail"].lower()

    def test_create_engagement_missing_required_fields(self, client):
        """Test creating engagement with missing required fields."""
        response = client.post("/api/v1/engagements", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListEngagements:
    """Tests for GET /api/v1/engagements"""

    def test_list_engagements_empty(self, client, db_session, sample_client_data):
        """Test listing engagements when none exist."""
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        response = client.get(f"/api/v1/engagements?client_id={client_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_engagements_with_data(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test listing engagements with data."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        # Create multiple engagements
        for i in range(3):
            engagement_data = sample_engagement_data.copy()
            engagement_data["client_id"] = client_id
            engagement_data["vat_period_start"] = f"2026-{i+1:02d}-01"
            client.post("/api/v1/engagements", json=engagement_data)
        
        response = client.get(f"/api/v1/engagements?client_id={client_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_engagements_pagination(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test engagement listing with pagination."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        # Create 5 engagements
        for i in range(5):
            engagement_data = sample_engagement_data.copy()
            engagement_data["client_id"] = client_id
            client.post("/api/v1/engagements", json=engagement_data)
        
        # Test pagination
        response = client.get(f"/api/v1/engagements?client_id={client_id}&skip=2&limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_list_engagements_client_not_found(self, client):
        """Test listing engagements for non-existent client."""
        response = client.get("/api/v1/engagements?client_id=99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetEngagement:
    """Tests for GET /api/v1/engagements/{engagement_id}"""

    def test_get_engagement_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test getting an engagement by ID."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        
        create_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = create_response.json()["id"]
        
        # Get engagement
        response = client.get(f"/api/v1/engagements/{engagement_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == engagement_id
        assert data["client_id"] == client_id

    def test_get_engagement_not_found(self, client):
        """Test getting non-existent engagement."""
        response = client.get("/api/v1/engagements/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateEngagement:
    """Tests for PATCH /api/v1/engagements/{engagement_id}"""

    def test_update_engagement_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test updating an engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        
        create_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = create_response.json()["id"]
        
        # Update engagement
        update_data = {"status": "locked"}
        response = client.patch(f"/api/v1/engagements/{engagement_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "locked"

    def test_update_engagement_not_found(self, client):
        """Test updating non-existent engagement."""
        update_data = {"status": "locked"}
        response = client.patch("/api/v1/engagements/99999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteEngagement:
    """Tests for DELETE /api/v1/engagements/{engagement_id}"""

    def test_delete_engagement_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test deleting an engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        
        create_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = create_response.json()["id"]
        
        # Delete engagement
        response = client.delete(f"/api/v1/engagements/{engagement_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deleted
        get_response = client.get(f"/api/v1/engagements/{engagement_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_engagement_not_found(self, client):
        """Test deleting non-existent engagement."""
        response = client.delete("/api/v1/engagements/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestLockEngagement:
    """Tests for POST /api/v1/engagements/{engagement_id}/lock"""

    def test_lock_engagement_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test locking an engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        
        create_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = create_response.json()["id"]
        
        # Lock engagement
        response = client.post(f"/api/v1/engagements/{engagement_id}/lock")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_locked"] is True

    def test_lock_engagement_not_found(self, client):
        """Test locking non-existent engagement."""
        response = client.post("/api/v1/engagements/99999/lock")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUnlockEngagement:
    """Tests for POST /api/v1/engagements/{engagement_id}/unlock"""

    def test_unlock_engagement_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test unlocking an engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        
        create_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = create_response.json()["id"]
        
        # Lock first
        client.post(f"/api/v1/engagements/{engagement_id}/lock")
        
        # Unlock engagement
        response = client.post(f"/api/v1/engagements/{engagement_id}/unlock")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_locked"] is False

    def test_unlock_engagement_not_found(self, client):
        """Test unlocking non-existent engagement."""
        response = client.post("/api/v1/engagements/99999/unlock")
        assert response.status_code == status.HTTP_404_NOT_FOUND
