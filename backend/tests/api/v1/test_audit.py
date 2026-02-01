"""Unit tests for Audit API endpoints."""

import pytest
from fastapi import status


class TestGetAuditByEngagement:
    """Tests for GET /api/v1/audit/engagement/{engagement_id}"""

    def test_get_audit_by_engagement_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test getting audit logs for an engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        
        response = client.get(f"/api/v1/audit/engagement/{engagement_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_audit_by_engagement_not_found(self, client):
        """Test getting audit logs for non-existent engagement."""
        response = client.get("/api/v1/audit/engagement/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_audit_by_engagement_pagination(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test getting audit logs with pagination."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        
        response = client.get(f"/api/v1/audit/engagement/{engagement_id}?skip=0&limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestGetAuditByClient:
    """Tests for GET /api/v1/audit/client/{client_id}"""

    def test_get_audit_by_client_success(self, client, db_session, sample_client_data):
        """Test getting audit logs for a client."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        response = client.get(f"/api/v1/audit/client/{client_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_audit_by_client_not_found(self, client):
        """Test getting audit logs for non-existent client."""
        response = client.get("/api/v1/audit/client/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_audit_by_client_pagination(self, client, db_session, sample_client_data):
        """Test getting audit logs with pagination."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        response = client.get(f"/api/v1/audit/client/{client_id}?skip=0&limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestGetAuditByEntity:
    """Tests for GET /api/v1/audit/entity/{entity_type}/{entity_id}"""

    def test_get_audit_by_entity_success(self, client, db_session, sample_client_data):
        """Test getting audit logs for a specific entity."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        response = client.get(f"/api/v1/audit/entity/client/{client_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_audit_by_entity_document(self, client, db_session, sample_client_data):
        """Test getting audit logs for a document entity."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        # Create document
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        from unittest.mock import patch
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc_id = sync_response.json()["document_id"]
            
            response = client.get(f"/api/v1/audit/entity/document/{doc_id}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "items" in data

    def test_get_audit_by_entity_pagination(self, client, db_session, sample_client_data):
        """Test getting audit logs with pagination."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        response = client.get(f"/api/v1/audit/entity/client/{client_id}?skip=0&limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
