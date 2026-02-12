"""Unit tests for Request Template API endpoints."""

import pytest
from fastapi import status
from datetime import date

from app.models.requests.template import RequestTemplate, RequestTemplateItem
from app.models.documents.type import DocumentCategory, DocumentType
from app.models.engagements.engagement import EngagementType


class TestListRequestTemplates:
    """Tests for GET /api/v1/requests/templates"""

    def test_list_templates_success(self, client, db_session):
        """Test listing all templates."""
        # Create a template
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        doc_type = DocumentType(
            category_id=category.id,
            code="TEST_DOC",
            name="Test Document",
            is_active=True,
        )
        db_session.add(doc_type)
        db_session.flush()
        
        template = RequestTemplate(
            name="Test Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        db_session.add(template)
        db_session.flush()
        
        item = RequestTemplateItem(
            template_id=template.id,
            document_type_id=doc_type.id,
            description="Test description",
            expected_count=1,
            is_required=True,
            order_index=1,
        )
        db_session.add(item)
        db_session.commit()
        
        response = client.get("/api/v1/requests/templates")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_templates_filter_by_client_type(self, client, db_session):
        """Test filtering templates by client type."""
        # Create templates with different client types
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        doc_type = DocumentType(
            category_id=category.id,
            code="TEST_DOC",
            name="Test Document",
            is_active=True,
        )
        db_session.add(doc_type)
        db_session.flush()
        
        template1 = RequestTemplate(
            name="Sole Trader Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        template2 = RequestTemplate(
            name="Limited Company Template",
            client_type="limited_company",
            engagement_type="vat_return",
            is_active=True,
        )
        db_session.add_all([template1, template2])
        db_session.commit()
        
        response = client.get("/api/v1/requests/templates?client_type=sole_trader")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(t["client_type"] == "sole_trader" for t in data["items"])

    def test_list_templates_filter_by_engagement_type(self, client, db_session):
        """Test filtering templates by engagement type."""
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        template1 = RequestTemplate(
            name="VAT Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        template2 = RequestTemplate(
            name="Accounts Template",
            client_type="sole_trader",
            engagement_type="annual_accounts",
            is_active=True,
        )
        db_session.add_all([template1, template2])
        db_session.commit()
        
        response = client.get("/api/v1/requests/templates?engagement_type=vat_return")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(t["engagement_type"] == "vat_return" for t in data["items"])

    def test_list_templates_filter_by_active(self, client, db_session):
        """Test filtering templates by active status."""
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        template1 = RequestTemplate(
            name="Active Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        template2 = RequestTemplate(
            name="Inactive Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=False,
        )
        db_session.add_all([template1, template2])
        db_session.commit()
        
        response = client.get("/api/v1/requests/templates?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(t["is_active"] is True for t in data["items"])


class TestGetRequestTemplate:
    """Tests for GET /api/v1/requests/templates/{template_id}"""

    def test_get_template_success(self, client, db_session):
        """Test getting a template by ID."""
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        doc_type = DocumentType(
            category_id=category.id,
            code="TEST_DOC",
            name="Test Document",
            is_active=True,
        )
        db_session.add(doc_type)
        db_session.flush()
        
        template = RequestTemplate(
            name="Test Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        db_session.add(template)
        db_session.flush()
        
        item = RequestTemplateItem(
            template_id=template.id,
            document_type_id=doc_type.id,
            description="Test description",
            expected_count=1,
            is_required=True,
            order_index=1,
        )
        db_session.add(item)
        db_session.commit()
        
        response = client.get(f"/api/v1/requests/templates/{template.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == template.id
        assert data["name"] == "Test Template"
        assert len(data["items"]) == 1

    def test_get_template_not_found(self, client):
        """Test getting non-existent template."""
        response = client.get("/api/v1/requests/templates/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateRequestSetFromTemplate:
    """Tests for POST /api/v1/requests/templates/{template_id}/create-set"""

    def test_create_request_set_from_template_success(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test creating a request set from a template."""
        # Create client with sole_trader type
        sample_client_data["client_type"] = "sole_trader"
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        assert client_response.status_code == status.HTTP_201_CREATED
        client_id = client_response.json()["id"]
        assert client_response.json()["client_type"] == "sole_trader"
        
        # Create engagement
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert engagement_response.status_code == status.HTTP_201_CREATED
        engagement_id = engagement_response.json()["id"]
        
        # Create template with items
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        doc_type = DocumentType(
            category_id=category.id,
            code="TEST_DOC",
            name="Test Document",
            is_active=True,
        )
        db_session.add(doc_type)
        db_session.flush()
        
        template = RequestTemplate(
            name="Test Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        db_session.add(template)
        db_session.flush()
        
        item = RequestTemplateItem(
            template_id=template.id,
            document_type_id=doc_type.id,
            description="Upload document for period [Q_START] to [Q_END]",
            expected_count=1,
            is_required=True,
            order_index=1,
        )
        db_session.add(item)
        db_session.commit()
        
        # Create request set from template
        create_data = {
            "engagement_id": engagement_id,
            "template_id": template.id,
        }
        response = client.post(f"/api/v1/requests/templates/{template.id}/create-set", json=create_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["engagement_id"] == engagement_id
        assert "Test Template" in data["name"]
        assert "id" in data
        
        # Verify request items were created
        items_response = client.get(f"/api/v1/requests/items?request_set_id={data['id']}")
        assert items_response.status_code == status.HTTP_200_OK
        items_data = items_response.json()
        assert items_data["total"] == 1
        # Check placeholder replacement
        assert "[Q_START]" not in items_data["items"][0]["description"]
        assert "[Q_END]" not in items_data["items"][0]["description"]

    def test_create_request_set_from_template_with_name_override(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test creating request set with custom name."""
        # Create client with sole_trader type
        sample_client_data["client_type"] = "sole_trader"
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        # Create template
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        template = RequestTemplate(
            name="Test Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        db_session.add(template)
        db_session.commit()
        
        # Create with name override
        create_data = {
            "engagement_id": engagement_id,
            "template_id": template.id,
            "name_override": "Custom Request Set Name",
        }
        response = client.post(f"/api/v1/requests/templates/{template.id}/create-set", json=create_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Custom Request Set Name"

    def test_create_request_set_template_not_found(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test creating request set from non-existent template."""
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        create_data = {
            "engagement_id": engagement_id,
            "template_id": 99999,
        }
        response = client.post("/api/v1/requests/templates/99999/create-set", json=create_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_request_set_engagement_not_found(self, client, db_session):
        """Test creating request set for non-existent engagement."""
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        template = RequestTemplate(
            name="Test Template",
            client_type="sole_trader",
            engagement_type="vat_return",
            is_active=True,
        )
        db_session.add(template)
        db_session.commit()
        
        create_data = {
            "engagement_id": 99999,
            "template_id": template.id,
        }
        response = client.post(f"/api/v1/requests/templates/{template.id}/create-set", json=create_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_request_set_client_type_mismatch(self, client, db_session, sample_client_data, sample_engagement_data):
        """Test creating request set when client type doesn't match template."""
        # Create client with limited_company type
        sample_client_data["client_type"] = "limited_company"
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        # Create engagement
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        # Create template for sole_trader
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        template = RequestTemplate(
            name="Sole Trader Template",
            client_type="sole_trader",  # Mismatch!
            engagement_type="vat_return",
            is_active=True,
        )
        db_session.add(template)
        db_session.commit()
        
        create_data = {
            "engagement_id": engagement_id,
            "template_id": template.id,
        }
        response = client.post(f"/api/v1/requests/templates/{template.id}/create-set", json=create_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "client_type" in response.json()["detail"].lower()

    def test_create_request_set_engagement_type_mismatch(self, client, db_session, sample_client_data):
        """Test creating request set when engagement type doesn't match template."""
        # Create client with sole_trader type (so we can test engagement_type mismatch)
        sample_client_data["client_type"] = "sole_trader"
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        
        engagement_data = {
            "client_id": client_id,
            "engagement_type": "annual_accounts",  # Different from template
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
        }
        engagement_response = client.post("/api/v1/engagements", json=engagement_data)
        engagement_id = engagement_response.json()["id"]
        
        # Create template for vat_return
        category = DocumentCategory(code="TEST", name="Test Category")
        db_session.add(category)
        db_session.flush()
        
        template = RequestTemplate(
            name="VAT Template",
            client_type="sole_trader",
            engagement_type="vat_return",  # Mismatch!
            is_active=True,
        )
        db_session.add(template)
        db_session.commit()
        
        create_data = {
            "engagement_id": engagement_id,
            "template_id": template.id,
        }
        response = client.post(f"/api/v1/requests/templates/{template.id}/create-set", json=create_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "engagement_type" in response.json()["detail"].lower()


class TestRequestItemStatusUpdate:
    """Tests for automatic request item status updates when documents are linked."""

    def test_request_item_status_updates_on_document_link(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test that request item status updates when document is linked."""
        # Create full chain
        client_response = client.post("/api/v1/clients", json=sample_client_data)
        client_id = client_response.json()["id"]
        sample_engagement_data["client_id"] = client_id
        engagement_response = client.post("/api/v1/engagements", json=sample_engagement_data)
        engagement_id = engagement_response.json()["id"]
        sample_request_set_data["engagement_id"] = engagement_id
        request_set_response = client.post("/api/v1/requests/sets", json=sample_request_set_data)
        request_set_id = request_set_response.json()["id"]
        
        # Set expected_count to 2
        sample_request_item_data["request_set_id"] = request_set_id
        sample_request_item_data["expected_count"] = 2
        request_item_response = client.post("/api/v1/requests/items", json=sample_request_item_data)
        request_item_id = request_item_response.json()["id"]
        
        # Verify initial status is PENDING
        item_response = client.get(f"/api/v1/requests/items/{request_item_id}")
        assert item_response.json()["status"] == "pending"
        
        # Create and link first document
        from unittest.mock import patch
        sync_data = {
            "filename": "test1.pdf",
            "external_url": "https://utfs.io/f/test-key-1",
            "client_id": client_id,
            "engagement_id": engagement_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc1_id = sync_response.json()["document_id"]
            
            # Link document directly
            link_response = client.post(f"/api/v1/requests/items/{request_item_id}/documents/{doc1_id}")
            assert link_response.status_code == status.HTTP_204_NO_CONTENT
            
            # Check status is now PARTIAL (1 of 2)
            item_response = client.get(f"/api/v1/requests/items/{request_item_id}")
            assert item_response.json()["status"] == "partial"
            
            # Link second document
            sync_data2 = {
                "filename": "test2.pdf",
                "external_url": "https://utfs.io/f/test-key-2",
                "client_id": client_id,
                "engagement_id": engagement_id,
            }
            sync_response2 = client.post("/api/v1/documents/sync", json=sync_data2)
            doc2_id = sync_response2.json()["document_id"]
            
            client.post(f"/api/v1/requests/items/{request_item_id}/documents/{doc2_id}")
            
            # Check status is now COMPLETE (2 of 2)
            item_response = client.get(f"/api/v1/requests/items/{request_item_id}")
            assert item_response.json()["status"] == "complete"

    def test_request_item_status_updates_on_document_unlink(self, client, db_session, sample_client_data, sample_engagement_data, sample_request_set_data, sample_request_item_data):
        """Test that request item status updates when document is unlinked."""
        # Create full chain and link document
        from unittest.mock import patch
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
        
        sync_data = {
            "filename": "test.pdf",
            "external_url": "https://utfs.io/f/test-key",
            "client_id": client_id,
            "engagement_id": engagement_id,
        }
        
        with patch("app.api.v1.documents.routes.run_process_document"):
            sync_response = client.post("/api/v1/documents/sync", json=sync_data)
            doc_id = sync_response.json()["document_id"]
            
            # Link document
            client.post(f"/api/v1/requests/items/{request_item_id}/documents/{doc_id}")
            
            # Verify status is COMPLETE
            item_response = client.get(f"/api/v1/requests/items/{request_item_id}")
            assert item_response.json()["status"] == "complete"
            
            # Unlink document
            client.delete(f"/api/v1/requests/items/{request_item_id}/documents/{doc_id}")
            
            # Verify status is back to PENDING
            item_response = client.get(f"/api/v1/requests/items/{request_item_id}")
            assert item_response.json()["status"] == "pending"
