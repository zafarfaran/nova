"""Unit tests for Chat API endpoints."""

import pytest
from fastapi import status
from unittest.mock import Mock, AsyncMock, patch


class TestCreateSession:
    """Tests for POST /api/v1/chat/sessions"""

    def test_create_session_success(self, client, db_session, sample_client_data):
        """Test creating a chat session."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        session_data = {
            "client_id": client_id,
            "title": "Test Chat Session"
        }
        
        response = client.post("/api/v1/chat/sessions", json=session_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["client_id"] == client_id
        assert data["title"] == "Test Chat Session"
        assert "id" in data

    def test_create_session_without_title(self, client, db_session, sample_client_data):
        """Test creating a chat session without title."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        session_data = {
            "client_id": client_id
        }
        
        response = client.post("/api/v1/chat/sessions", json=session_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "title" in data


class TestListSessions:
    """Tests for GET /api/v1/chat/sessions"""

    def test_list_sessions_empty(self, client):
        """Test listing sessions when none exist."""
        response = client.get("/api/v1/chat/sessions")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_list_sessions_with_data(self, client, db_session, sample_client_data):
        """Test listing sessions with data."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        # Create multiple sessions
        for i in range(3):
            session_data = {
                "client_id": client_id,
                "title": f"Session {i+1}"
            }
            client.post("/api/v1/chat/sessions", json=session_data)
        
        response = client.get("/api/v1/chat/sessions?limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 3


class TestGetSession:
    """Tests for GET /api/v1/chat/sessions/{session_id}"""

    def test_get_session_success(self, client, db_session, sample_client_data):
        """Test getting a chat session."""
        # Create client and session
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        session_data = {
            "client_id": client_id,
            "title": "Test Session"
        }
        create_response = client.post("/api/v1/chat/sessions", json=session_data)
        session_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/chat/sessions/{session_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == session_id

    def test_get_session_not_found(self, client):
        """Test getting non-existent session."""
        response = client.get("/api/v1/chat/sessions/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetMessages:
    """Tests for GET /api/v1/chat/sessions/{session_id}/messages"""

    def test_get_messages_success(self, client, db_session, sample_client_data):
        """Test getting messages for a session."""
        # Create client and session
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        session_data = {
            "client_id": client_id,
            "title": "Test Session"
        }
        create_response = client.post("/api/v1/chat/sessions", json=session_data)
        session_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/chat/sessions/{session_id}/messages")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_get_messages_session_not_found(self, client):
        """Test getting messages for non-existent session."""
        response = client.get("/api/v1/chat/sessions/99999/messages")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChat:
    """Tests for POST /api/v1/chat/sessions/{session_id}/chat"""

    @patch("app.services.chat.service.ChatService.chat")
    def test_chat_success(self, mock_chat, client, db_session, sample_client_data):
        """Test sending a chat message."""
        mock_chat.return_value = "AI response"
        
        # Create client and session
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        session_data = {
            "client_id": client_id,
            "title": "Test Session"
        }
        create_response = client.post("/api/v1/chat/sessions", json=session_data)
        session_id = create_response.json()["id"]
        
        chat_data = {
            "message": "Hello, how can you help?"
        }
        
        response = client.post(f"/api/v1/chat/sessions/{session_id}/chat", json=chat_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == session_id
        assert "response" in data
        assert "messages" in data

    def test_chat_session_not_found(self, client):
        """Test sending message to non-existent session."""
        chat_data = {
            "message": "Hello"
        }
        response = client.post("/api/v1/chat/sessions/99999/chat", json=chat_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChatStream:
    """Tests for POST /api/v1/chat/stream"""

    @patch("app.services.chat.service.ChatService.chat_stream")
    def test_chat_stream_success(self, mock_stream, client):
        """Test streaming chat response."""
        # Mock the stream generator
        async def mock_generator():
            yield "data: Hello\n\n"
            yield "data: World\n\n"
        
        mock_stream.return_value = mock_generator()
        
        stream_data = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
        
        response = client.post("/api/v1/chat/stream", json=stream_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @patch("app.services.chat.service.ChatService.chat_stream")
    def test_chat_stream_empty_messages(self, mock_stream, client):
        """Test streaming with empty messages."""
        # Mock the stream generator to handle empty messages gracefully
        async def mock_generator():
            yield "data: No messages provided\n\n"
        
        mock_stream.return_value = mock_generator()
        
        stream_data = {
            "messages": []
        }
        
        response = client.post("/api/v1/chat/stream", json=stream_data)
        # Should handle empty messages gracefully (either 200 with mock or 400/422 from validation)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
