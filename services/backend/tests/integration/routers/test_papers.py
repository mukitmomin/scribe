"""
Integration tests for Papers API endpoints.
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from app.models import Paper


@pytest.mark.integration
class TestPapersAPI:
    """Test suite for /api/v1/papers endpoints."""

    @pytest.fixture
    async def create_test_paper(self, test_db):
        """Create a test paper in the database."""
        paper = Paper(
            id="2401.12345",
            title="Test Paper",
            authors=["John Doe"],
            summary="Test summary",
            published_date=datetime(2024, 1, 15),
            pdf_url="https://arxiv.org/pdf/2401.12345.pdf",
            status="new",
            is_bookmarked=False,
        )
        test_db.add(paper)
        await test_db.commit()
        await test_db.refresh(paper)
        return paper

    def test_health_check(self, client):
        """Test that API is accessible."""
        response = client.get("/")
        assert response.status_code in [200, 404]  # Either root exists or not

    @pytest.mark.asyncio
    async def test_toggle_bookmark(self, client, create_test_paper):
        """Test toggling bookmark status for a paper."""
        paper = await create_test_paper

        # Toggle to True
        response = client.put(f"/api/v1/papers/{paper.id}/bookmark")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["is_bookmarked"] is True

        # Toggle to False
        response = client.put(f"/api/v1/papers/{paper.id}/bookmark")
        assert response.status_code == 200
        data = response.json()
        assert data["is_bookmarked"] is False

    def test_toggle_bookmark_not_found(self, client):
        """Test bookmarking a non-existent paper."""
        response = client.put("/api/v1/papers/9999.99999/bookmark")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_bookmarks_empty(self, client):
        """Test fetching bookmarks when none exist."""
        response = client.get("/api/v1/papers/bookmarks")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_bookmarks(self, client, create_test_paper):
        """Test fetching bookmarked papers."""
        # Create and bookmark a paper
        paper = await create_test_paper
        client.put(f"/api/v1/papers/{paper.id}/bookmark")

        # Fetch bookmarks
        response = client.get("/api/v1/papers/bookmarks")
        assert response.status_code == 200
        bookmarks = response.json()
        assert len(bookmarks) >= 1
        assert any(p["id"] == paper.id for p in bookmarks)

    @patch("app.routers.v1.papers.arxiv_service.search_papers")
    def test_get_trending_papers(self, mock_search, client):
        """Test fetching trending papers."""
        # Setup mock
        mock_search.return_value = [
            {
                "id": "2401.11111",
                "title": "Trending Paper 1",
                "authors": ["Author A"],
                "summary": "Summary 1",
                "published_date": datetime(2024, 1, 10),
                "pdf_url": "https://arxiv.org/pdf/2401.11111.pdf",
                "status": "new",
            }
        ]

        # Execute
        response = client.get("/api/v1/papers/trending")
        assert response.status_code == 200
        papers = response.json()
        assert len(papers) >= 1

    @patch("app.routers.v1.papers.arxiv_service.search_papers")
    def test_get_trending_papers_with_query(self, mock_search, client):
        """Test trending papers with custom query."""
        mock_search.return_value = []

        response = client.get("/api/v1/papers/trending?q=transformers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("app.routers.v1.papers.arxiv_service.search_papers")
    def test_get_trending_papers_with_topic(self, mock_search, client):
        """Test trending papers with topic filter."""
        mock_search.return_value = []

        response = client.get("/api/v1/papers/trending?topic=LLMs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("app.routers.v1.papers.arxiv_service.search_papers")
    def test_get_trending_papers_with_sort(self, mock_search, client):
        """Test trending papers with sort parameter."""
        mock_search.return_value = []

        response = client.get("/api/v1/papers/trending?sort=relevance")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        # Verify sort parameter was passed to service
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs.get("sort_by") == "relevance"

    @patch("app.agents.researcher.researcher_graph.ainvoke")
    def test_discover_papers(self, mock_agent, client):
        """Test paper discovery endpoint."""
        # Setup mock
        mock_agent.return_value = {
            "found_papers": [
                {
                    "id": "2401.22222",
                    "title": "Discovered Paper",
                    "authors": ["Researcher B"],
                    "summary": "Discovered summary",
                    "published_date": datetime(2024, 1, 20),
                    "pdf_url": "https://arxiv.org/pdf/2401.22222.pdf",
                    "status": "new",
                }
            ]
        }

        # Execute
        response = client.get("/api/v1/papers/discover")
        assert response.status_code == 200
        papers = response.json()

        # The papers should be saved to DB and returned
        assert isinstance(papers, list)

    @patch("app.agents.researcher.researcher_graph.ainvoke")
    def test_discover_papers_with_query(self, mock_agent, client):
        """Test discovery with user query."""
        mock_agent.return_value = {"found_papers": []}

        response = client.get("/api/v1/papers/discover?q=neural+networks")
        assert response.status_code == 200

        # Verify agent was called with query
        mock_agent.assert_called_once()
        call_args = mock_agent.call_args[0][0]
        assert "neural networks" in call_args.get("user_query", "")
