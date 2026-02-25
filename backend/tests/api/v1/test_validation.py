"""Unit tests for Validation API endpoints."""

import pytest
from fastapi import status
from unittest.mock import Mock, patch


class TestRunValidation:
    """Tests for POST /api/v1/validation/run/{doc_id}"""

    def test_run_validation_success(self, client, db_session, sample_client_data):
        """Test running validation on a document."""
        # Create client and document
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            assert sync_response.status_code == status.HTTP_200_OK, f"Document sync failed: {sync_response.json()}"
            doc_id = sync_response.json()["document_id"]
            
            # Run validation
            response = client.post(f"/api/v1/validation/run/{doc_id}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["document_id"] == doc_id
            assert "results" in data
            assert "passed" in data
            assert "failed" in data

    def test_run_validation_document_not_found(self, client):
        """Test running validation on non-existent document."""
        response = client.post("/api/v1/validation/run/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetValidationResults:
    """Tests for GET /api/v1/validation/results/{doc_id}"""

    def test_get_validation_results_success(self, client, db_session, sample_client_data):
        """Test getting validation results."""
        # Create client and document
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            assert sync_response.status_code == status.HTTP_200_OK, f"Document sync failed: {sync_response.json()}"
            doc_id = sync_response.json()["document_id"]
            
            # Get validation results
            response = client.get(f"/api/v1/validation/results/{doc_id}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "items" in data
            assert "total" in data

    def test_get_validation_results_document_not_found(self, client):
        """Test getting validation results for non-existent document."""
        response = client.get("/api/v1/validation/results/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetValidationSummary:
    """Tests for GET /api/v1/validation/summary/{engagement_id}"""

    def test_get_validation_summary_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test getting validation summary."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        
        # Get validation summary
        response = client.get(f"/api/v1/validation/summary/{engagement_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "engagement_id" in data
        assert "total_documents" in data
        assert "validated_documents" in data
        assert "failed_documents" in data
        assert "pending_documents" in data
        assert "total_validations" in data
        assert "passed_validations" in data
        assert "failed_validations" in data
        assert "warning_validations" in data
        assert "validation_rate" in data

    def test_get_validation_summary_engagement_not_found(self, client):
        """Test getting validation summary for non-existent engagement."""
        response = client.get("/api/v1/validation/summary/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunEngagementValidation:
    """Tests for POST /api/v1/validation/run-engagement/{engagement_id}"""

    def test_run_engagement_validation_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test running validation on all documents in an engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        
        with patch("app.tasks.validation_tasks.validate_engagement_documents"):
            response = client.post(f"/api/v1/validation/run-engagement/{engagement_id}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["engagement_id"] == engagement_id
            assert "message" in data

    def test_run_engagement_validation_not_found(self, client):
        """Test running validation for non-existent engagement."""
        response = client.post("/api/v1/validation/run-engagement/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunClientValidation:
    """Tests for POST /api/v1/validation/run/client/{client_id}"""

    def test_run_client_validation_success(self, client, db_session, sample_client_data):
        """Test running validation on all documents for a client."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        with patch("app.tasks.validation.validate_client_documents"):
            response = client.post(f"/api/v1/validation/run/client/{client_id}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["client_id"] == client_id
            assert "message" in data

    def test_run_client_validation_not_found(self, client):
        """Test running validation for non-existent client."""
        response = client.post("/api/v1/validation/run/client/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRejectDocument:
    """Tests for POST /api/v1/validation/reject/{doc_id}"""

    def test_reject_document_success(self, client, db_session, sample_client_data):
        """Test rejecting a document."""
        # Create client and document
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            assert sync_response.status_code == status.HTTP_200_OK, f"Document sync failed: {sync_response.json()}"
            doc_id = sync_response.json()["document_id"]
            
            # Reject document
            rejection_data = {
                "rejected_by": "test@example.com",
                "rejection_reason": "Invalid format"
            }
            
            with patch("app.services.email.EmailNotificationService.send_document_rejection_email") as mock_email:
                mock_email.return_value = True
                response = client.post(f"/api/v1/validation/reject/{doc_id}", json=rejection_data)
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["document_id"] == doc_id
                assert data["rejected_by"] == "test@example.com"

    def test_reject_document_not_found(self, client):
        """Test rejecting non-existent document."""
        rejection_data = {
            "rejected_by": "test@example.com",
            "rejection_reason": "Invalid format"
        }
        response = client.post("/api/v1/validation/reject/99999", json=rejection_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
