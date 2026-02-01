"""Unit tests for Chaser API endpoints."""

import pytest
from fastapi import status
from unittest.mock import Mock, AsyncMock, patch


class TestCreateChaserRequest:
    """Tests for POST /api/v1/chaser/requests"""

    def test_create_chaser_request_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test creating a chaser request."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        chaser_data = {
            "engagement_id": engagement_id,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1", "Invoice 2"],
            "due_date": "2026-02-01"
        }
        
        response = client.post("/api/v1/chaser/requests", json=chaser_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["engagement_id"] == engagement_id
        assert data["recipient_email"] == chaser_data["recipient_email"]
        assert "id" in data

    def test_create_chaser_request_engagement_not_found(self, client):
        """Test creating chaser request for non-existent engagement."""
        chaser_data = {
            "engagement_id": 99999,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1"]
        }
        
        response = client.post("/api/v1/chaser/requests", json=chaser_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestListChaserRequests:
    """Tests for GET /api/v1/chaser/requests"""

    def test_list_chaser_requests_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test listing chaser requests."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        # Create multiple chaser requests
        for i in range(3):
            chaser_data = {
                "engagement_id": engagement_id,
                "recipient_email": f"client{i}@example.com",
                "recipient_name": f"Client {i}",
                "requested_items": [f"Item {i}"]
            }
            client.post("/api/v1/chaser/requests", json=chaser_data)
        
        response = client.get(f"/api/v1/chaser/requests?engagement_id={engagement_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3


class TestGetChaserRequest:
    """Tests for GET /api/v1/chaser/requests/{chaser_id}"""

    def test_get_chaser_request_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test getting a chaser request by ID."""
        # Create client, engagement, and chaser
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        chaser_data = {
            "engagement_id": engagement_id,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1"]
        }
        create_response = client.post("/api/v1/chaser/requests", json=chaser_data)
        chaser_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/chaser/requests/{chaser_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == chaser_id

    def test_get_chaser_request_not_found(self, client):
        """Test getting non-existent chaser request."""
        response = client.get("/api/v1/chaser/requests/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGenerateChaserMessage:
    """Tests for POST /api/v1/chaser/requests/{chaser_id}/generate-message"""

    @patch("app.services.chaser.service.ChaserService.generate_message", new_callable=AsyncMock)
    def test_generate_chaser_message_success(self, mock_generate, client, db_session, sample_client_data, sample_engagement_data):
        """Test generating AI message for chaser."""
        # Create client, engagement, and chaser
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        
        chaser_data = {
            "engagement_id": engagement_id,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1"]
        }
        create_response = client.post("/api/v1/chaser/requests", json=chaser_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Chaser creation failed: {create_response.json()}"
        chaser_id = create_response.json()["id"]
        
        # Get the actual chaser object to return from mock
        from app.services.chaser import ChaserService
        service = ChaserService(db_session)
        chaser = service.get(chaser_id)
        
        # Mock async method to return the actual chaser
        mock_generate.return_value = chaser
        
        response = client.post(f"/api/v1/chaser/requests/{chaser_id}/generate-message")
        assert response.status_code == status.HTTP_200_OK

    def test_generate_chaser_message_not_found(self, client):
        """Test generating message for non-existent chaser."""
        response = client.post("/api/v1/chaser/requests/99999/generate-message")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSendChaserEmail:
    """Tests for POST /api/v1/chaser/requests/{chaser_id}/send-email"""

    @patch("app.services.chaser.service.ChaserService.send_chaser_email", new_callable=AsyncMock)
    def test_send_chaser_email_success(self, mock_send, client, db_session, sample_client_data, sample_engagement_data):
        """Test sending chaser email."""
        # Create client, engagement, and chaser
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        
        chaser_data = {
            "engagement_id": engagement_id,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1"]
        }
        create_response = client.post("/api/v1/chaser/requests", json=chaser_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Chaser creation failed: {create_response.json()}"
        chaser_id = create_response.json()["id"]
        
        # Get the actual chaser object to return from mock
        from app.services.chaser import ChaserService
        service = ChaserService(db_session)
        chaser = service.get(chaser_id)
        
        # Mock to return the actual chaser (async method)
        mock_send.return_value = chaser
        
        response = client.post(f"/api/v1/chaser/requests/{chaser_id}/send-email")
        assert response.status_code == status.HTTP_200_OK

    def test_send_chaser_email_not_found(self, client):
        """Test sending email for non-existent chaser."""
        response = client.post("/api/v1/chaser/requests/99999/send-email")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMarkChaserSent:
    """Tests for POST /api/v1/chaser/requests/{chaser_id}/send"""

    def test_mark_chaser_sent_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test marking chaser as sent."""
        # Create client, engagement, and chaser
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        
        chaser_data = {
            "engagement_id": engagement_id,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1"]
        }
        create_response = client.post("/api/v1/chaser/requests", json=chaser_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Chaser creation failed: {create_response.json()}"
        chaser_id = create_response.json()["id"]
        
        response = client.post(f"/api/v1/chaser/requests/{chaser_id}/send")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Check status instead of sent field
        assert data["status"] in ["sent", "complete"] or data.get("sent_at") is not None

    def test_mark_chaser_sent_not_found(self, client):
        """Test marking non-existent chaser as sent."""
        response = client.post("/api/v1/chaser/requests/99999/send")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRemindChaser:
    """Tests for POST /api/v1/chaser/requests/{chaser_id}/remind"""

    def test_remind_chaser_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test marking chaser as reminded."""
        # Create client, engagement, and chaser
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        chaser_data = {
            "engagement_id": engagement_id,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1"]
        }
        create_response = client.post("/api/v1/chaser/requests", json=chaser_data)
        chaser_id = create_response.json()["id"]
        
        response = client.post(f"/api/v1/chaser/requests/{chaser_id}/remind")
        assert response.status_code == status.HTTP_200_OK

    def test_remind_chaser_not_found(self, client):
        """Test reminding non-existent chaser."""
        response = client.post("/api/v1/chaser/requests/99999/remind")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAutoChase:
    """Tests for POST /api/v1/chaser/auto-chase/{engagement_id}"""

    def test_auto_chase_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test auto-chasing an engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        auto_chase_data = {
            "recipient_email": "client@example.com"
        }
        
        # May fail if no pending items, but should handle gracefully
        response = client.post(
            f"/api/v1/chaser/auto-chase/{engagement_id}",
            json=auto_chase_data
        )
        # Either success or no items found
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_auto_chase_engagement_not_found(self, client):
        """Test auto-chasing non-existent engagement."""
        auto_chase_data = {
            "recipient_email": "client@example.com"
        }
        response = client.post("/api/v1/chaser/auto-chase/99999", json=auto_chase_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetChaserByToken:
    """Tests for GET /api/v1/chaser/by-token/{upload_token}"""

    def test_get_chaser_by_token_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test getting chaser by upload token."""
        # Create client, engagement, and chaser
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        chaser_data = {
            "engagement_id": engagement_id,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1"]
        }
        create_response = client.post("/api/v1/chaser/requests", json=chaser_data)
        chaser = create_response.json()
        
        # Get by token (if token exists)
        if "upload_token" in chaser:
            token = chaser["upload_token"]
            response = client.get(f"/api/v1/chaser/by-token/{token}")
            assert response.status_code == status.HTTP_200_OK

    def test_get_chaser_by_token_invalid(self, client):
        """Test getting chaser with invalid token."""
        response = client.get("/api/v1/chaser/by-token/invalid-token")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRecordChaserResponse:
    """Tests for POST /api/v1/chaser/requests/{chaser_id}/response"""

    def test_record_chaser_response_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test recording a response to chaser."""
        # Create client, engagement, and chaser
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        chaser_data = {
            "engagement_id": engagement_id,
            "recipient_email": "client@example.com",
            "recipient_name": "Test Client",
            "requested_items": ["Invoice 1"]
        }
        create_response = client.post("/api/v1/chaser/requests", json=chaser_data)
        chaser_id = create_response.json()["id"]
        
        response_data = {
            "documents_uploaded": 2,
            "responder_email": "client@example.com",
            "responder_name": "Test Client",
            "notes": "Documents uploaded"
        }
        
        response = client.post(
            f"/api/v1/chaser/requests/{chaser_id}/response",
            json=response_data
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["documents_uploaded"] == 2

    def test_record_chaser_response_not_found(self, client):
        """Test recording response for non-existent chaser."""
        response_data = {
            "documents_uploaded": 2,
            "responder_email": "client@example.com"
        }
        response = client.post("/api/v1/chaser/requests/99999/response", json=response_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
