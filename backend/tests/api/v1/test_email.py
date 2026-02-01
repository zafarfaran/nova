"""Unit tests for Email API endpoints."""

import pytest
from fastapi import status
from unittest.mock import Mock, AsyncMock, patch


class TestSendEmail:
    """Tests for POST /api/v1/email/send"""

    @patch("app.services.email.service.EmailService.send_email")
    def test_send_email_success(self, mock_send, client, db_session, sample_client_data):
        """Test sending an email."""
        mock_send.return_value = {
            "success": True,
            "message": "Email sent successfully",
            "message_id": "test-message-id",
            "generated_subject": "Test Subject",
            "generated_body": "Test Body",
            "sent_at": "2026-01-01T00:00:00Z"
        }
        
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        email_data = {
            "to_email": "recipient@example.com",
            "to_name": "Test Recipient",
            "purpose": "reminder",
            "tone": "friendly",
            "client_id": client_id,
            "context_data": {
                "reminder_type": "document upload"
            }
        }
        
        response = client.post("/api/v1/email/send", json=email_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "message_id" in data

    @patch("app.services.email.service.EmailService.send_email")
    def test_send_email_with_subject_and_body(self, mock_send, client, db_session, sample_client_data):
        """Test sending email with provided subject and body."""
        mock_send.return_value = {
            "success": True,
            "message": "Email sent successfully",
            "message_id": "test-message-id",
            "generated_subject": "Custom Subject",
            "generated_body": "Custom Body",
            "sent_at": "2026-01-01T00:00:00Z"
        }
        
        email_data = {
            "to_email": "recipient@example.com",
            "to_name": "Test Recipient",
            "subject": "Custom Subject",
            "body": "Custom Body"
        }
        
        response = client.post("/api/v1/email/send", json=email_data)
        assert response.status_code == status.HTTP_200_OK

    @patch("app.services.email.service.EmailService.send_email")
    def test_send_email_validation_error(self, mock_send, client):
        """Test sending email with validation error."""
        mock_send.side_effect = ValueError("Invalid email address")
        
        # Use valid schema data so it reaches the service layer
        # The service will raise ValueError which should return 400
        email_data = {
            "to_email": "valid@example.com",
            "purpose": "reminder"
        }
        
        response = client.post("/api/v1/email/send", json=email_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("app.services.email.service.EmailService.send_email")
    def test_send_email_service_error(self, mock_send, client):
        """Test sending email with service error."""
        mock_send.side_effect = Exception("SMTP connection failed")
        
        email_data = {
            "to_email": "recipient@example.com",
            "purpose": "reminder"
        }
        
        response = client.post("/api/v1/email/send", json=email_data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestPreviewEmail:
    """Tests for POST /api/v1/email/preview"""

    @patch("app.services.email.service.EmailService.generate_preview")
    def test_preview_email_success(self, mock_preview, client, db_session, sample_client_data):
        """Test generating email preview."""
        mock_preview.return_value = {
            "subject": "Preview Subject",
            "body": "Preview Body"
        }
        
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        response = client.post(
            "/api/v1/email/preview",
            params={
                "purpose": "reminder",
                "tone": "friendly",
                "client_id": client_id,
                "context_data": '{"reminder_type": "document upload"}'
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "subject" in data
        assert "body" in data

    @patch("app.services.email.service.EmailService.generate_preview")
    def test_preview_email_without_client(self, mock_preview, client):
        """Test generating email preview without client."""
        mock_preview.return_value = {
            "subject": "Preview Subject",
            "body": "Preview Body"
        }
        
        response = client.post(
            "/api/v1/email/preview",
            params={
                "purpose": "reminder",
                "tone": "friendly"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    @patch("app.services.email.service.EmailService.generate_preview")
    def test_preview_email_validation_error(self, mock_preview, client):
        """Test preview with validation error."""
        mock_preview.side_effect = ValueError("Invalid purpose")
        
        # Use valid schema data so it reaches the service layer
        # The service will raise ValueError which should return 400
        response = client.post(
            "/api/v1/email/preview",
            params={
                "purpose": "reminder",  # Valid enum value
                "tone": "friendly"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("app.services.email.service.EmailService.generate_preview")
    def test_preview_email_service_error(self, mock_preview, client):
        """Test preview with service error."""
        mock_preview.side_effect = Exception("AI provider error")
        
        response = client.post(
            "/api/v1/email/preview",
            params={
                "purpose": "reminder",
                "tone": "friendly"
            }
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
