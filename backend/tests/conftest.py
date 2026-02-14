"""Pytest configuration and shared fixtures."""

import os
import uuid
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

# Load .env file from backend directory
# pydantic-settings includes python-dotenv, so this should work
try:
    from dotenv import load_dotenv
    
    # Get the backend directory (parent of tests directory)
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"[TEST] Loaded .env file from: {env_file}")
    else:
        print(f"[TEST] Warning: .env file not found at {env_file}")
        print(f"[TEST] Make sure .env file exists in: {backend_dir}")
except ImportError:
    # python-dotenv not available, but pydantic-settings should handle it
    print("[TEST] Note: python-dotenv not available, relying on pydantic-settings for .env loading")

from app.main import app
from app.core.database import get_db
from app.ai.provider import AIProvider


@pytest.fixture(scope="session")
def test_database():
    """Set up test database from TEST_DATABASE_URL environment variable."""
    # Get test database URL from environment (should be set in .env file)
    test_db_url = os.getenv("TEST_DATABASE_URL")
    
    if not test_db_url:
        error_msg = (
            f"\n{'='*70}\n"
            f"❌ ERROR: TEST_DATABASE_URL environment variable is not set.\n\n"
            f"Please set TEST_DATABASE_URL in your .env file or environment:\n"
            f"   TEST_DATABASE_URL=postgresql://user:password@host:5432/database_name\n\n"
            f"Example for local PostgreSQL:\n"
            f"   TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nova_test\n\n"
            f"Example for Supabase test project:\n"
            f"   TEST_DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres\n"
            f"{'='*70}\n"
        )
        pytest.exit(error_msg)
    
    # Ensure postgresql:// prefix
    if test_db_url.startswith("postgres://"):
        test_db_url = test_db_url.replace("postgres://", "postgresql://", 1)
    
    # Validate it's a PostgreSQL URL
    if not test_db_url.startswith("postgresql://"):
        error_msg = (
            f"\n{'='*70}\n"
            f"❌ ERROR: TEST_DATABASE_URL must be a PostgreSQL connection string.\n"
            f"Current value: {test_db_url}\n"
            f"Expected format: postgresql://user:password@host:5432/database\n"
            f"{'='*70}\n"
        )
        pytest.exit(error_msg)
    
    print(f"\n[TEST] Using test database: {test_db_url.split('@')[1] if '@' in test_db_url else 'configured database'}")
    yield test_db_url


def _create_enum_types(engine):
    """Create PostgreSQL ENUM types if they don't exist."""
    with engine.connect() as conn:
        # Create all ENUM types used by the models
        # Using DO blocks to handle "already exists" gracefully
        enums = [
            ("entitytype", ["'SOLE_TRADER'", "'PARTNERSHIP'", "'LLP'", "'LIMITED_COMPANY'", "'PLC'", "'CHARITY'", "'OTHER'"]),
            ("engagementtype", ["'vat_return'", "'annual_accounts'", "'tax_return'", "'audit'", "'bookkeeping'", "'other'"]),
            ("engagementstatus", ["'draft'", "'in_progress'", "'under_review'", "'ready'", "'submitted'", "'locked'"]),
            ("counterpartytype", ["'supplier'", "'customer'", "'both'"]),
            ("accounttype", ["'bank_current'", "'bank_savings'", "'credit_card'", "'payment_processor'", "'merchant'", "'other'"]),
            ("requestsetstatus", ["'draft'", "'sent'", "'partial'", "'complete'", "'expired'"]),
            ("requestitemstatus", ["'pending'", "'partial'", "'complete'", "'waived'"]),
            ("extractionstatus", ["'pending'", "'processing'", "'extracted'", "'failed'"]),
            ("documentstatus", ["'pending'", "'processing'", "'extracted'", "'validated'", "'failed'"]),
            ("chaserstatus", ["'draft'", "'sent'", "'reminded'", "'complete'", "'expired'"]),
            ("messagerole", ["'user'", "'assistant'", "'system'", "'tool'"]),
            ("ruletype", ["'vat_number_format'", "'vat_number_valid'", "'date_range'", "'amount_range'", "'required_field'", "'account_holder_match'"]),
            ("validationstatus", ["'passed'", "'failed'", "'warning'", "'skipped'"]),
        ]
        
        for enum_name, enum_values in enums:
            values_str = ", ".join(enum_values)
            sql = f"""
            DO $$ 
            BEGIN 
                CREATE TYPE {enum_name} AS ENUM ({values_str}); 
            EXCEPTION 
                WHEN duplicate_object THEN NULL; 
            END $$;
            """
            try:
                conn.execute(sqlalchemy.text(sql))
                conn.commit()
            except Exception as e:
                # Ignore errors - enum might already exist or we don't have permission
                # In that case, SQLAlchemy will handle it when creating tables
                pass


# Global engine and sessionmaker (shared across tests in a session)
_test_engine = None
_test_sessionmaker = None


@pytest.fixture(scope="session")
def test_engine(test_database: str):
    """Create database engine and tables once per test session."""
    global _test_engine, _test_sessionmaker
    from app.models.base import Base
    import sqlalchemy
    
    # Import all models to ensure metadata is loaded
    import app.models.clients.client  # noqa: F401
    import app.models.engagements.engagement  # noqa: F401
    import app.models.documents.document  # noqa: F401
    import app.models.requests.set  # noqa: F401
    import app.models.requests.item  # noqa: F401
    import app.models.validation.validation  # noqa: F401
    import app.models.chat.chat  # noqa: F401
    import app.models.chaser.chaser  # noqa: F401
    import app.models.audit.log  # noqa: F401
    
    # Create engine with test database
    _test_engine = create_engine(
        test_database,
        poolclass=NullPool,  # No connection pooling for tests
        echo=False,
    )
    
    # Create ENUM types before creating tables
    try:
        _create_enum_types(_test_engine)
    except Exception as e:
        # If we can't create ENUMs (permission issue), try to continue anyway
        print(f"[TEST] Warning: Could not create ENUM types: {e}")
        print("[TEST] Attempting to create tables anyway...")
    
    # Create all tables once for the entire test session
    Base.metadata.create_all(bind=_test_engine)
    
    # Create sessionmaker
    _test_sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
    
    yield _test_engine
    
    # Cleanup after all tests complete
    Base.metadata.drop_all(bind=_test_engine)
    _test_engine.dispose()
    _test_engine = None
    _test_sessionmaker = None


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test with transaction rollback."""
    global _test_sessionmaker
    
    if _test_sessionmaker is None:
        pytest.fail("test_engine fixture must be set up first")
    
    # Create a new session for this test
    # With autocommit=False, a transaction is automatically started
    session = _test_sessionmaker()
    
    # Override commit() to just flush, so we can always rollback
    # This prevents actual commits while still allowing flush operations
    original_commit = session.commit
    
    def test_commit():
        """Override commit to flush only, preventing actual commits."""
        session.flush()  # Flush changes but don't commit
    
    session.commit = test_commit
    
    try:
        yield session
    finally:
        # Restore original commit method
        session.commit = original_commit
        # Rollback all changes (this will work because we never actually committed)
        try:
            session.rollback()
        except Exception:
            pass
        # Close the session
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_ai_provider() -> Mock:
    """Create a mock AI provider."""
    provider = Mock(spec=AIProvider)
    provider.generate_text = AsyncMock(return_value="Generated text")
    provider.chat = AsyncMock(return_value="Chat response")
    provider.chat_stream = AsyncMock()
    return provider


@pytest.fixture
def mock_email_service() -> Mock:
    """Create a mock email service."""
    service = Mock()
    service.send_email = AsyncMock(return_value={
        "success": True,
        "message": "Email sent successfully",
        "message_id": "test-message-id",
        "generated_subject": "Test Subject",
        "generated_body": "Test Body",
        "sent_at": "2026-01-01T00:00:00Z"
    })
    service.generate_preview = AsyncMock(return_value={
        "subject": "Test Subject",
        "body": "Test Body"
    })
    return service


@pytest.fixture
def mock_chat_service() -> Mock:
    """Create a mock chat service."""
    service = Mock()
    service.create_session = Mock(return_value=Mock(id=1, client_id=1, title="Test Session"))
    service.get_session = Mock(return_value=Mock(id=1, client_id=1, title="Test Session"))
    service.list_sessions = Mock(return_value=[])
    service.get_messages = Mock(return_value=[])
    service.chat = AsyncMock(return_value="AI response")
    service.chat_stream = AsyncMock()
    return service


@pytest.fixture
def sample_client_data() -> dict:
    """Sample client data for testing with unique VAT number per test."""
    # Generate unique VAT number for each test to avoid conflicts
    unique_id = str(uuid.uuid4())[:8].replace("-", "").upper()
    return {
        "name": f"Test Client Ltd {unique_id}",
        "contact_email": f"test-{unique_id}@example.com",
        "entity_type": "limited_company",
        "vat_number": f"GB{unique_id}",
    }


@pytest.fixture
def sample_engagement_data() -> dict:
    """Sample engagement data for testing."""
    return {
        "client_id": 1,
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
        "status": "draft",
    }


@pytest.fixture
def sample_document_data() -> dict:
    """Sample document data for testing."""
    return {
        "filename": "test_invoice.pdf",
        "s3_key": "test-key",
        "file_hash": "test-hash",
        "content_type": "application/pdf",
        "file_size": 1024,
        "client_id": 1,
        "engagement_id": 1,
    }


@pytest.fixture
def sample_request_set_data() -> dict:
    """Sample request set data for testing."""
    return {
        "engagement_id": 1,
        "name": "Q1 2026 Documents",
    }


@pytest.fixture
def sample_document_type(db_session):
    """Create a sample document category and type for testing."""
    from app.models.documents.type import DocumentCategory, DocumentType
    
    # Generate unique codes to avoid conflicts
    unique_id = str(uuid.uuid4())[:8].replace("-", "").upper()
    
    # Create category
    category = DocumentCategory(
        code=f"test_category_{unique_id}",
        name="Test Category"
    )
    db_session.add(category)
    db_session.flush()
    
    # Create document type
    doc_type = DocumentType(
        category_id=category.id,
        code=f"test_invoice_{unique_id}",
        name="Test Invoice"
    )
    db_session.add(doc_type)
    db_session.flush()
    
    return doc_type


@pytest.fixture
def sample_request_item_data(sample_document_type) -> dict:
    """Sample request item data for testing."""
    return {
        "request_set_id": 1,
        "document_type_id": sample_document_type.id,
        "description": "Invoice for January",
        "is_required": True,
    }
