"""
Unit tests for ArxivService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.arxiv_service import ArxivService
from app.models import Paper


@pytest.mark.unit
class TestArxivService:
    """Test suite for ArxivService."""

    @pytest.fixture
    def service(self):
        """Create an ArxivService instance."""
        return ArxivService()

    @pytest.fixture
    def mock_arxiv_result(self):
        """Create a mock arxiv.Result object."""
        mock_result = Mock()
        mock_result.get_short_id.return_value = "2401.12345v1"
        mock_result.title = "Test Paper Title"
        mock_result.authors = [Mock(name="John Doe"), Mock(name="Jane Smith")]
        mock_result.summary = "This is a test paper summary."
        mock_result.published = datetime(2024, 1, 15)
        mock_result.pdf_url = "https://arxiv.org/pdf/2401.12345.pdf"
        return mock_result

    @patch("app.services.arxiv_service.arxiv.Client")
    def test_search_papers_standard_query(self, mock_client_class, service, mock_arxiv_result):
        """Test standard search query."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.results.return_value = [mock_arxiv_result]

        # Execute
        results = service.search_papers(query="machine learning", max_results=5)

        # Assert
        assert len(results) == 1
        assert results[0]["id"] == "2401.12345"
        assert results[0]["title"] == "Test Paper Title"
        assert results[0]["authors"] == ["John Doe", "Jane Smith"]
        assert results[0]["summary"] == "This is a test paper summary."
        assert results[0]["status"] == "new"

    @patch("app.services.arxiv_service.arxiv.Client")
    def test_search_papers_by_id(self, mock_client_class, service, mock_arxiv_result):
        """Test searching by paper ID."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.results.return_value = [mock_arxiv_result]

        # Execute
        results = service.search_papers(query="2401.12345")

        # Assert
        assert len(results) == 1
        assert results[0]["id"] == "2401.12345"

    @patch("app.services.arxiv_service.arxiv.Client")
    def test_search_papers_by_url(self, mock_client_class, service, mock_arxiv_result):
        """Test searching by arxiv URL."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.results.return_value = [mock_arxiv_result]

        # Execute
        results = service.search_papers(query="http://arxiv.org/abs/2401.12345")

        # Assert
        assert len(results) == 1
        assert results[0]["id"] == "2401.12345"

    @patch("app.services.arxiv_service.arxiv.Client")
    def test_search_papers_handles_error(self, mock_client_class, service):
        """Test that search handles errors gracefully."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.results.side_effect = Exception("Network error")

        # Execute
        results = service.search_papers(query="test")

        # Assert - should return empty list on error
        assert results == []

    @pytest.mark.asyncio
    async def test_save_papers_new_papers(self, service, test_db, sample_paper_data):
        """Test saving new papers to database."""
        # Execute
        await service.save_papers(test_db, [sample_paper_data])

        # Assert
        result = await test_db.execute(
            f"SELECT * FROM papers WHERE id = '{sample_paper_data['id']}'"
        )
        paper = result.first()
        assert paper is not None

    @pytest.mark.asyncio
    async def test_save_papers_ignores_duplicates(self, service, test_db, sample_paper_data):
        """Test that duplicate papers are ignored."""
        # Execute - save twice
        await service.save_papers(test_db, [sample_paper_data])
        await service.save_papers(test_db, [sample_paper_data])

        # Assert - should only have one paper
        from sqlalchemy import select
        result = await test_db.execute(select(Paper).where(Paper.id == sample_paper_data["id"]))
        papers = result.scalars().all()
        assert len(papers) == 1

    @pytest.mark.asyncio
    async def test_get_paper_details_from_db(self, service, test_db, sample_paper_data):
        """Test fetching paper details from database."""
        # Setup - save paper first
        await service.save_papers(test_db, [sample_paper_data])

        # Execute
        result = await service.get_paper_details(test_db, sample_paper_data["id"])

        # Assert
        assert result is not None
        assert result["id"] == sample_paper_data["id"]
        assert result["title"] == sample_paper_data["title"]
        assert result["authors"] == sample_paper_data["authors"]

    @pytest.mark.asyncio
    @patch("app.services.arxiv_service.arxiv.Client")
    async def test_get_paper_details_fallback_to_arxiv(
        self, mock_client_class, service, test_db
    ):
        """Test fetching paper details from arxiv when not in DB."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_result = Mock()
        mock_result.title = "Fallback Paper"
        mock_result.authors = [Mock(name="Author One")]
        mock_result.summary = "Summary from arxiv"
        mock_result.published = datetime(2024, 2, 1)
        mock_result.pdf_url = "https://arxiv.org/pdf/2402.00001.pdf"

        mock_client.results.return_value = iter([mock_result])

        # Execute
        result = await service.get_paper_details(test_db, "2402.00001")

        # Assert
        assert result is not None
        assert result["id"] == "2402.00001"
        assert result["title"] == "Fallback Paper"

    @pytest.mark.asyncio
    @patch("app.services.arxiv_service.arxiv.Client")
    async def test_get_paper_details_not_found(
        self, mock_client_class, service, test_db
    ):
        """Test fetching paper that doesn't exist."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.results.return_value = iter([])  # Empty iterator

        # Execute
        result = await service.get_paper_details(test_db, "9999.99999")

        # Assert
        assert result is None
