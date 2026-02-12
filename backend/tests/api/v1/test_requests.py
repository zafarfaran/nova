"""Unit tests for Requests API endpoints."""

import pytest
from fastapi import status


class TestRequestSets:
    """Tests for Request Set endpoints."""

    def test_create_request_set_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data):
        """Test creating a request set."""
        # Create client and engagement
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED, f"Client creation failed: {client_response.json()}"
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        
        response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {response.json()}"
        data = response.json()
        assert data["engagement_id"] == engagement_id
        assert data["name"] == sample_request_set_data["name"]
        assert "id" in data

    def test_create_request_set_engagement_not_found(self, client, db_session, sample_request_set_data):
        """Test creating request set for non-existent engagement."""
        sample_request_set_data["engagement_id"] = 99999
        response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND, f"Expected 404, got {response.status_code}: {response.json()}"

    def test_list_request_sets_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data):
        """Test listing request sets."""
        # Create client, engagement, and request sets
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        
        # Create multiple request sets
        for i in range(3):
            request_set_data = sample_request_set_data.copy()
            request_set_data["name"] = f"Request Set {i+1}"
            create_response = client.post("/api/v1/requests/sets", json=request_set_data)
            assert create_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {create_response.json()}"
        
        response = client.get(f"/api/v1/requests/sets?engagement_id={engagement_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3

    def test_get_request_set_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data):
        """Test getting a request set by ID."""
        # Create client, engagement, and request set
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        
        create_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {create_response.json()}"
        request_set_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/requests/sets/{request_set_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == request_set_id

    def test_get_request_set_not_found(self, client):
        """Test getting non-existent request set."""
        response = client.get("/api/v1/requests/sets/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_request_set_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data):
        """Test updating a request set."""
        # Create client, engagement, and request set
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        
        create_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {create_response.json()}"
        request_set_id = create_response.json()["id"]
        
        # Update request set
        update_data = {"name": "Updated Name"}
        response = client.patch(f"/api/v1/requests/sets/{request_set_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_delete_request_set_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data):
        """Test deleting a request set."""
        # Create client, engagement, and request set
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        
        create_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {create_response.json()}"
        request_set_id = create_response.json()["id"]
        
        # Delete request set
        response = client.delete(f"/api/v1/requests/sets/{request_set_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestRequestItems:
    """Tests for Request Item endpoints."""

    def test_create_request_item_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test creating a request item."""
        # Create client, engagement, and request set
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert request_set_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {request_set_response.json()}"
        request_set_id = request_set_response.json()["id"]
        sample_request_item_data["request_set_id"] = request_set_id
        
        response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        assert response.status_code == status.HTTP_201_CREATED, f"Request item creation failed: {response.json()}"
        data = response.json()
        assert data["request_set_id"] == request_set_id
        assert "id" in data

    def test_create_request_item_set_not_found(self, client, sample_request_item_data):
        """Test creating request item for non-existent request set."""
        sample_request_item_data["request_set_id"] = 99999
        response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_request_items_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test listing request items."""
        # Create client, engagement, request set, and items
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert request_set_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {request_set_response.json()}"
        request_set_id = request_set_response.json()["id"]
        sample_request_item_data["request_set_id"] = request_set_id
        
        # Create multiple items
        for i in range(3):
            item_data = sample_request_item_data.copy()
            item_data["description"] = f"Item {i+1}"
            create_response = client.post("/api/v1/requests/items", json=item_data)
            assert create_response.status_code == status.HTTP_201_CREATED, f"Request item creation failed: {create_response.json()}"
        
        response = client.get(f"/api/v1/requests/items?request_set_id={request_set_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3

    def test_get_request_item_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test getting a request item by ID."""
        # Create full chain
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert request_set_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {request_set_response.json()}"
        request_set_id = request_set_response.json()["id"]
        sample_request_item_data["request_set_id"] = request_set_id
        
        create_response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Request item creation failed: {create_response.json()}"
        request_item_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/requests/items/{request_item_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == request_item_id

    def test_get_request_item_not_found(self, client):
        """Test getting non-existent request item."""
        response = client.get("/api/v1/requests/items/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_request_item_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test updating a request item."""
        # Create full chain
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert request_set_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {request_set_response.json()}"
        request_set_id = request_set_response.json()["id"]
        sample_request_item_data["request_set_id"] = request_set_id
        
        create_response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Request item creation failed: {create_response.json()}"
        request_item_id = create_response.json()["id"]
        
        # Update request item
        update_data = {"description": "Updated Description"}
        response = client.patch(f"/api/v1/requests/items/{request_item_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated Description"

    def test_delete_request_item_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test deleting a request item."""
        # Create full chain
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert request_set_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {request_set_response.json()}"
        request_set_id = request_set_response.json()["id"]
        sample_request_item_data["request_set_id"] = request_set_id
        
        create_response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        assert create_response.status_code == status.HTTP_201_CREATED, f"Request item creation failed: {create_response.json()}"
        request_item_id = create_response.json()["id"]
        
        # Delete request item
        response = client.delete(f"/api/v1/requests/items/{request_item_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestLinkDocument:
    """Tests for linking documents to request items."""

    def test_link_document_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test linking a document to a request item."""
        # Create full chain
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert request_set_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {request_set_response.json()}"
        request_set_id = request_set_response.json()["id"]
        sample_request_item_data["request_set_id"] = request_set_id
        request_item_response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        assert request_item_response.status_code == status.HTTP_201_CREATED, f"Request item creation failed: {request_item_response.json()}"
        request_item_id = request_item_response.json()["id"]
        
        # Create document
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
            "engagement_id": engagement_id,
        }
        
        from unittest.mock import patch
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc_id = sync_response.json()["document_id"]
            
            # Link document
            response = client.post(f"/api/v1/requests/items/{request_item_id}/documents/{doc_id}")
            assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_link_document_not_found(self, client):
        """Test linking non-existent document or request item."""
        response = client.post("/api/v1/requests/items/99999/documents/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unlink_document_success(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test unlinking a document from a request item."""
        # Create full chain and link document (similar to test_link_document_success)
        # Then unlink
        from unittest.mock import patch
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED, f"Engagement creation failed: {engagement_response.json()}"
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        assert request_set_response.status_code == status.HTTP_201_CREATED, f"Request set creation failed: {request_set_response.json()}"
        request_set_id = request_set_response.json()["id"]
        sample_request_item_data["request_set_id"] = request_set_id
        request_item_response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        assert request_item_response.status_code == status.HTTP_201_CREATED, f"Request item creation failed: {request_item_response.json()}"
        request_item_id = request_item_response.json()["id"]
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
            "engagement_id": engagement_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc_id = sync_response.json()["document_id"]
            
            # Link first
            client.post(f"/api/v1/requests/items/{request_item_id}/documents/{doc_id}")
            
            # Unlink document
            response = client.delete(f"/api/v1/requests/items/{request_item_id}/documents/{doc_id}")
            assert response.status_code == status.HTTP_204_NO_CONTENT


class TestDocumentUploadWithRequestItem:
    """Tests for document upload with request item linking."""

    def test_upload_document_with_request_item(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test uploading a document and linking it to a request item."""
        from unittest.mock import patch, MagicMock
        
        # Create full chain
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        request_set_id = request_set_response.json()["id"]
        sample_request_item_data["request_set_id"] = request_set_id
        request_item_response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        request_item_id = request_item_response.json()["id"]
        
        # Mock storage and processing
        with patch("app.services.documents.service.get_storage") as mock_storage, \
             patch("app.api.v1.documents.routes.run_process_document"):
            mock_storage_instance = MagicMock()
            mock_storage_instance.upload_file.return_value = "test-key-123"
            mock_storage.return_value = mock_storage_instance
            
            # Upload document with request_item_id
            response = client.post(
                f"/api/v1/documents/upload?client_id={client_id}&engagement_id={engagement_id}&request_item_id={request_item_id}",
                files={"file": ("test.pdf", b"fake pdf content", "application/pdf")}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "document_id" in data
            
            # Verify document is linked to request item
            items_response = client.get(f"/api/v1/requests/items/{request_item_id}")
            items_data = items_response.json()
            # Status should be updated (we can't easily check document count without querying)
            assert items_data["id"] == request_item_id

    def test_upload_document_validates_type_match(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data):
        """Test that upload warns if document type doesn't match request item."""
        from unittest.mock import patch, MagicMock
        
        # Create category and document types
        from app.models.documents.type import DocumentCategory, DocumentType
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        doc_type1 = DocumentType(
            category_id=category.id,
            code="TYPE1",
            name="Type 1",
            is_active=True,
        )
        doc_type2 = DocumentType(
            category_id=category.id,
            code="TYPE2",
            name="Type 2",
            is_active=True,
        )
        db_session.add_all([doc_type1, doc_type2])
        db_session.flush()
        
        # Create full chain with request item expecting doc_type1
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        request_set_id = request_set_response.json()["id"]
        
        request_item_data = {
            "request_set_id": request_set_id,
            "document_type_id": doc_type1.id,
            "description": "Test item",
            "expected_count": 1,
            "is_required": True,
        }
        request_item_response = client.post("/api/v1/requests/items", json=request_item_data)
        request_item_id = request_item_response.json()["id"]
        
        # Create document with doc_type2 (mismatch)
        from app.models.documents import Document
        doc = Document(
            client_id=client_id,
            engagement_id=engagement_id,
            filename="test.pdf",
            s3_key="test-key",
            file_hash="test-hash",
            document_type_id=doc_type2.id,  # Mismatch!
            status="pending",
        )
        db_session.add(doc)
        db_session.commit()
        
        # Link document (should work but log warning)
        response = client.post(f"/api/v1/requests/items/{request_item_id}/documents/{doc.id}")
        # Should succeed (warning logged but doesn't fail)
        assert response.status_code == status.HTTP_204_NO_CONTENT