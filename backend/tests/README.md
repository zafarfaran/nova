# API Tests

This directory contains comprehensive unit tests for all API v1 endpoints.

## Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── api/
│   └── v1/
│       ├── test_clients.py      # Client management endpoints
│       ├── test_engagements.py  # Engagement endpoints
│       ├── test_documents.py    # Document management endpoints
│       ├── test_validation.py   # Validation endpoints
│       ├── test_requests.py     # Request set/item endpoints
│       ├── test_chat.py         # Chat endpoints
│       ├── test_email.py        # Email endpoints
│       ├── test_chaser.py       # Chaser endpoints
│       └── test_audit.py        # Audit log endpoints
└── README.md                # This file
```

## Setup

Before running tests, you need to configure a test database. Add the following to your `.env` file in the `backend` directory:

```env
TEST_DATABASE_URL=postgresql://user:password@host:5432/database_name
```

**Examples:**

For local PostgreSQL:
```env
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nova_test
```

For Supabase test project:
```env
TEST_DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
```

**Important:** The test database should be separate from your production/development database to avoid data conflicts.

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run specific test file
```bash
pytest tests/api/v1/test_clients.py
```

### Run specific test class
```bash
pytest tests/api/v1/test_clients.py::TestCreateClient
```

### Run specific test
```bash
pytest tests/api/v1/test_clients.py::TestCreateClient::test_create_client_success
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run with verbose output
```bash
pytest -v
```

## Test Coverage

The test suite covers:

### Clients API (`/api/v1/clients`)
- ✅ Create client (with duplicate VAT number handling)
- ✅ List clients (with pagination)
- ✅ Get client by ID
- ✅ Update client (partial updates)
- ✅ Delete client
- ✅ Onboarding completion

### Engagements API (`/api/v1/engagements`)
- ✅ Create engagement
- ✅ List engagements (with pagination)
- ✅ Get engagement by ID
- ✅ Update engagement
- ✅ Delete engagement
- ✅ Lock/unlock engagement

### Documents API (`/api/v1/documents`)
- ✅ Sync document from external storage
- ✅ Upload document
- ✅ List documents (by client/engagement/request item)
- ✅ Get document by ID
- ✅ Update document
- ✅ Delete document
- ✅ Process document
- ✅ Get extracted data
- ✅ Process all documents for engagement

### Validation API (`/api/v1/validation`)
- ✅ Run validation on document
- ✅ Get validation results
- ✅ Get validation summary
- ✅ Run validation for engagement/client
- ✅ Reject document

### Requests API (`/api/v1/requests`)
- ✅ Create/list/get/update/delete request sets
- ✅ Create/list/get/update/delete request items
- ✅ Link/unlink documents to request items

### Chat API (`/api/v1/chat`)
- ✅ Create/list/get chat sessions
- ✅ Get messages
- ✅ Send chat message
- ✅ Stream chat response

### Email API (`/api/v1/email`)
- ✅ Send email (with AI generation)
- ✅ Preview email

### Chaser API (`/api/v1/chaser`)
- ✅ Create/list/get chaser requests
- ✅ Generate chaser message
- ✅ Send chaser email
- ✅ Mark chaser as sent/reminded
- ✅ Auto-chase engagement
- ✅ Get chaser by token
- ✅ Record chaser response

### Audit API (`/api/v1/audit`)
- ✅ Get audit logs by engagement
- ✅ Get audit logs by client
- ✅ Get audit logs by entity (with pagination)

## Test Fixtures

The `conftest.py` file provides the following fixtures:

- `db_session`: In-memory SQLite database session for each test
- `client`: FastAPI TestClient with database override
- `mock_ai_provider`: Mock AI provider for testing
- `mock_email_service`: Mock email service
- `mock_chat_service`: Mock chat service
- `sample_client_data`: Sample client data
- `sample_engagement_data`: Sample engagement data
- `sample_document_data`: Sample document data
- `sample_request_set_data`: Sample request set data
- `sample_request_item_data`: Sample request item data

## Test Database

Tests use a PostgreSQL database configured via the `TEST_DATABASE_URL` environment variable. The test setup:
- Creates all tables before each test session
- Uses transactions for test isolation (rollback after each test)
- Drops all tables after each test for clean state
- Requires PostgreSQL (matches production environment)

**Note:** Make sure your test database is separate from production/development to avoid data loss.

## Mocking

The tests use `unittest.mock` to mock:
- External services (AI providers, email services)
- Background tasks
- File uploads
- External API calls

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Fixtures**: Use fixtures for common setup/teardown
3. **Assertions**: Test both success and error cases
4. **Coverage**: Aim for high coverage of edge cases
5. **Naming**: Use descriptive test names that explain what is being tested

## Adding New Tests

When adding new endpoints:

1. Create test class for the endpoint group
2. Test all HTTP methods (GET, POST, PATCH, DELETE)
3. Test success cases
4. Test error cases (404, 400, 422, etc.)
5. Test edge cases (pagination, filtering, etc.)
6. Use appropriate fixtures from `conftest.py`

Example:
```python
class TestNewEndpoint:
    """Tests for POST /api/v1/new-endpoint"""
    
    def test_new_endpoint_success(self, client, db_session):
        """Test successful request."""
        response = client.post("/api/v1/new-endpoint", json={...})
        assert response.status_code == status.HTTP_200_OK
    
    def test_new_endpoint_not_found(self, client):
        """Test error case."""
        response = client.post("/api/v1/new-endpoint/99999", json={...})
        assert response.status_code == status.HTTP_404_NOT_FOUND
```
