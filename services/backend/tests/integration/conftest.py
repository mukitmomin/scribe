"""
Integration test fixtures that use the real PostgreSQL database.

These fixtures are for integration tests that need to test against
the actual database running in Docker, not SQLite in-memory.

Prerequisites:
    - PostgreSQL running on localhost:5432 (via docker-compose)
    - Database initialized with schema (init.sql)

Usage:
    pytest tests/integration/ -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client():
    """
    Create a test client that uses the real database connection.
    
    This is for integration tests that test against the actual PostgreSQL
    database (via docker-compose). The NullPool in database.py ensures
    each request gets a fresh connection, avoiding async conflicts.
    
    Requires: 
        - Docker database running: docker compose up -d db
        - Environment configured for PostgreSQL (not SQLite)
    """
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


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
