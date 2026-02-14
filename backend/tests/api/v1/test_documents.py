"""Unit tests for Documents API endpoints."""

import pytest
from fastapi import status
from io import BytesIO
from unittest.mock import Mock, patch

from app.models.documents import Document, DocumentStatus


class TestSyncDocument:
    """Tests for POST /api/v1/documents/sync"""

    def test_sync_document_success(self, client, db_session, sample_client_data):
        """Test syncing a document from external storage."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "file_size": 1024,
            "content_type": "application/pdf",
            "client_id": client_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            response = client.post("/api/v1/documents/sync", json=sync_data)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["document_id"] is not None

    def test_sync_document_duplicate(self, client, db_session, sample_client_data):
        """Test syncing duplicate document."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        # Sync first time
        with patch("app.api.v1.documents.routes.run_process_document"):
            client.post("/api/v1/documents/sync", json=sync_data)
        
        # Sync again (should return existing)
        with patch("app.api.v1.documents.routes.run_process_document"):
            response = client.post("/api/v1/documents/sync", json=sync_data)
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["message"] == "Document already synced"


class TestUploadDocument:
    """Tests for POST /api/v1/documents/upload"""

    @patch("app.services.documents.service.DocumentService.upload")
    def test_upload_document_success(self, mock_upload, client, db_session, sample_client_data):
        """Test uploading a document."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        # Mock document service
        mock_doc = Mock()
        mock_doc.id = 1
        mock_doc.filename = "test.pdf"
        mock_doc.status = DocumentStatus.PENDING
        mock_upload.return_value = (mock_doc, False)
        
        file_content = BytesIO(b"fake pdf content")
        files = {"file": ("test.pdf", file_content, "application/pdf")}
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            response = client.post(
                f"/api/v1/documents/upload?client_id={client_id}",
                files=files
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["document_id"] == 1
            assert data["filename"] == "test.pdf"

    @patch("app.services.documents.service.DocumentService.upload")
    def test_upload_document_duplicate(self, mock_upload, client, db_session, sample_client_data):
        """Test uploading duplicate document."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        # Mock duplicate
        mock_doc = Mock()
        mock_doc.id = 1
        mock_doc.filename = "test.pdf"
        mock_doc.status = DocumentStatus.PENDING
        mock_upload.return_value = (mock_doc, True)  # is_duplicate=True
        
        file_content = BytesIO(b"fake pdf content")
        files = {"file": ("test.pdf", file_content, "application/pdf")}
        
        response = client.post(
            f"/api/v1/documents/upload?client_id={client_id}",
            files=files
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_duplicate"] is True


class TestListDocuments:
    """Tests for GET /api/v1/documents"""

    def test_list_documents_by_client(self, client, db_session, sample_client_data):
        """Test listing documents by client."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        response = client.get(f"/api/v1/documents?client_id={client_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_documents_by_engagement(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test listing documents by engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        response = client.get(f"/api/v1/documents?engagement_id={engagement_id}")
        assert response.status_code == status.HTTP_200_OK

    def test_list_documents_missing_filter(self, client):
        """Test listing documents without required filter."""
        response = client.get("/api/v1/documents")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGetDocument:
    """Tests for GET /api/v1/documents/{doc_id}"""

    def test_get_document_success(self, client, db_session, sample_client_data):
        """Test getting a document by ID."""
        # Create client
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        # Sync a document
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc_id = sync_response.json()["document_id"]
            
            # Get document
            response = client.get(f"/api/v1/documents/{doc_id}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == doc_id

    def test_get_document_not_found(self, client):
        """Test getting non-existent document."""
        response = client.get("/api/v1/documents/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateDocument:
    """Tests for PATCH /api/v1/documents/{doc_id}"""

    def test_update_document_success(self, client, db_session, sample_client_data):
        """Test updating a document."""
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
            
            # Update document (DocumentUpdate schema only supports engagement_id, document_type_id, status)
            update_data = {"status": "validated"}
            response = client.patch(f"/api/v1/documents/{doc_id}", json=update_data)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "validated"

    def test_update_document_not_found(self, client):
        """Test updating non-existent document."""
        update_data = {"filename": "updated.pdf"}
        response = client.patch("/api/v1/documents/99999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteDocument:
    """Tests for DELETE /api/v1/documents/{doc_id}"""

    def test_delete_document_success(self, client, db_session, sample_client_data):
        """Test deleting a document."""
        # Create client and document
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc_id = sync_response.json()["document_id"]
            
            # Delete document
            response = client.delete(f"/api/v1/documents/{doc_id}")
            assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_document_not_found(self, client):
        """Test deleting non-existent document."""
        response = client.delete("/api/v1/documents/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProcessDocument:
    """Tests for POST /api/v1/documents/{doc_id}/process"""

    def test_process_document_success(self, client, db_session, sample_client_data):
        """Test processing a document."""
        # Create client and document
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc_id = sync_response.json()["document_id"]
            
            # Process document
            with patch("app.api.v1.documents.routes.run_process_document") as mock_process:
                response = client.post(f"/api/v1/documents/{doc_id}/process")
                assert response.status_code == status.HTTP_200_OK
                mock_process.assert_called_once()

    def test_process_document_not_found(self, client):
        """Test processing non-existent document."""
        response = client.post("/api/v1/documents/99999/process")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetExtractedData:
    """Tests for GET /api/v1/documents/{doc_id}/extracted-data"""

    def test_get_extracted_data_success(self, client, db_session, sample_client_data):
        """Test getting extracted data."""
        # Create client and document
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc_id = sync_response.json()["document_id"]
            
            # Get extracted data
            response = client.get(f"/api/v1/documents/{doc_id}/extracted-data")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "invoice_number" in data
            assert "raw_data" in data

    def test_get_extracted_data_not_found(self, client):
        """Test getting extracted data for non-existent document."""
        response = client.get("/api/v1/documents/99999/extracted-data")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProcessAllDocuments:
    """Tests for POST /api/v1/documents/process-all/{engagement_id}"""

    def test_process_all_documents_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test processing all documents for an engagement."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            response = client.post(f"/api/v1/documents/process-all/{engagement_id}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True

    def test_process_all_documents_engagement_not_found(self, client):
        """Test processing all documents for non-existent engagement."""
        response = client.post("/api/v1/documents/process-all/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
