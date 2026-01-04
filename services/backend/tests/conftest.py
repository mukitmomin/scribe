"""
Pytest configuration and shared fixtures for the Scribe backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import Settings


@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with a test database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_settings():
    """Provide mock settings for testing."""
    return Settings(
        database_url="sqlite:///:memory:",
        google_api_key="test-api-key",
        use_mock_llm=True,  # Always use mock LLM in tests
        multi_tenant_enabled=False,
        default_tenant_id="test-tenant",
    )


@pytest.fixture
def sample_paper_data():
    """Sample paper data for testing."""
    return {
        "id": "2401.12345",
        "title": "A Novel Approach to Machine Learning",
        "authors": ["John Doe", "Jane Smith"],
        "summary": "This paper presents a groundbreaking approach to ML.",
        "published_date": "2024-01-15",
        "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
    }


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "role": "user",
        "content": "Explain the main contribution of this paper.",
    }
