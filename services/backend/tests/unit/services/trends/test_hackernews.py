"""
Unit tests for HackerNews trend source.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.trends.sources.hackernews import HackerNewsSource
from app.services.trends.models import TrendSignal


@pytest.mark.unit
class TestHackerNewsSource:
    """Test suite for HackerNewsSource."""

    @pytest.fixture
    def source(self):
        """Create a HackerNewsSource instance."""
        return HackerNewsSource()

    def test_extract_paper_id_from_abs_url(self, source):
        """Test extracting paper ID from arxiv.org/abs URL."""
        url = "https://arxiv.org/abs/2401.12345"
        paper_id = source.extract_paper_id(url)
        assert paper_id == "2401.12345"

    def test_extract_paper_id_from_pdf_url(self, source):
        """Test extracting paper ID from arxiv.org/pdf URL."""
        url = "https://arxiv.org/pdf/2401.12345.pdf"
        paper_id = source.extract_paper_id(url)
        assert paper_id == "2401.12345"

    def test_extract_paper_id_with_version(self, source):
        """Test extracting paper ID with version number."""
        url = "https://arxiv.org/abs/2401.12345v2"
        paper_id = source.extract_paper_id(url)
        assert paper_id == "2401.12345"

    def test_extract_paper_id_from_title_brackets(self, source):
        """Test extracting paper ID from title with brackets."""
        title = "New LLM Paper [2401.12345]"
        paper_id = source.extract_paper_id(title)
        assert paper_id == "2401.12345"

    def test_extract_paper_id_from_arxiv_prefix(self, source):
        """Test extracting paper ID from arxiv: prefix."""
        text = "Check out arxiv:2401.12345 for details"
        paper_id = source.extract_paper_id(text)
        assert paper_id == "2401.12345"

    def test_extract_paper_id_not_found(self, source):
        """Test when no paper ID is present."""
        text = "This is just a regular title"
        paper_id = source.extract_paper_id(text)
        assert paper_id is None

    def test_extract_paper_id_empty_string(self, source):
        """Test with empty string."""
        paper_id = source.extract_paper_id("")
        assert paper_id is None

    def test_compute_engagement_score(self, source):
        """Test engagement score computation."""
        signal = TrendSignal(
            source="hackernews",
            paper_id="2401.12345",
            paper_title="Test Paper",
            discussion_url="https://news.ycombinator.com/item?id=123",
            timestamp=datetime.now(),
            upvotes=100,
            comments=50,
        )

        score = source.compute_engagement_score(signal)

        # Formula: (upvotes + comments * 2) / 500 * 100
        # (100 + 50 * 2) / 500 * 100 = 200 / 500 * 100 = 40
        assert score == 40.0

    def test_compute_engagement_score_viral(self, source):
        """Test engagement score for viral post."""
        signal = TrendSignal(
            source="hackernews",
            paper_id="2401.12345",
            paper_title="Viral Paper",
            discussion_url="https://news.ycombinator.com/item?id=123",
            timestamp=datetime.now(),
            upvotes=500,
            comments=250,
        )

        score = source.compute_engagement_score(signal)

        # (500 + 250 * 2) / 500 * 100 = 1000 / 500 * 100 = 200
        # But capped at 100
        assert score == 100.0

    def test_matches_topic_llm(self, source):
        """Test topic matching for LLM."""
        story = {
            "title": "New Large Language Model Architecture",
            "url": "https://arxiv.org/abs/2401.12345",
        }

        assert source._matches_topic(story, "llm") is True

    def test_matches_topic_genai(self, source):
        """Test topic matching for GenAI."""
        story = {
            "title": "Improved Diffusion Models for Image Generation",
            "url": "https://example.com",
        }

        assert source._matches_topic(story, "genai") is True

    def test_matches_topic_no_match(self, source):
        """Test when topic doesn't match."""
        story = {
            "title": "Database Optimization Techniques",
            "url": "https://example.com",
        }

        assert source._matches_topic(story, "llm") is False

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_trending_basic(self, mock_client_class, source):
        """Test fetching trending papers from HackerNews."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock responses
        mock_client.get.side_effect = [
            # First call: get top stories
            Mock(
                json=lambda: [123, 456],
                raise_for_status=lambda: None,
            ),
            # Second call: story 123 (arXiv paper)
            Mock(
                json=lambda: {
                    "id": 123,
                    "type": "story",
                    "by": "user1",
                    "time": int(datetime.now().timestamp()),
                    "title": "Interesting AI Paper",
                    "url": "https://arxiv.org/abs/2401.12345",
                    "score": 150,
                    "descendants": 42,
                    "kids": [],
                },
                raise_for_status=lambda: None,
            ),
            # Third call: story 456 (not arXiv)
            Mock(
                json=lambda: {
                    "id": 456,
                    "type": "story",
                    "by": "user2",
                    "time": int(datetime.now().timestamp()),
                    "title": "Regular Story",
                    "url": "https://example.com",
                    "score": 100,
                    "descendants": 10,
                },
                raise_for_status=lambda: None,
            ),
        ]

        # Execute
        signals = await source.fetch_trending(max_results=10)

        # Assert
        assert len(signals) == 1
        assert signals[0].paper_id == "2401.12345"
        assert signals[0].source == "hackernews"
        assert signals[0].upvotes == 150
        assert signals[0].comments == 42
        assert "hackernews" in signals[0].discussion_url

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_trending_with_cache(self, mock_client_class, source):
        """Test that caching works."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # First fetch
        mock_client.get.side_effect = [
            Mock(json=lambda: [123], raise_for_status=lambda: None),
            Mock(
                json=lambda: {
                    "id": 123,
                    "time": int(datetime.now().timestamp()),
                    "title": "Paper",
                    "url": "https://arxiv.org/abs/2401.12345",
                    "score": 100,
                    "descendants": 10,
                },
                raise_for_status=lambda: None,
            ),
        ]

        signals1 = await source.fetch_trending(topic="AI", max_results=10)

        # Second fetch (should use cache)
        signals2 = await source.fetch_trending(topic="AI", max_results=10)

        # Should get same results without additional API calls
        assert len(signals1) == len(signals2)
        assert signals1[0].paper_id == signals2[0].paper_id

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_trending_filters_old_stories(self, mock_client_class, source):
        """Test that old stories are filtered out."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Story from 30 days ago
        old_timestamp = int((datetime.now().timestamp()) - (30 * 24 * 3600))

        mock_client.get.side_effect = [
            Mock(json=lambda: [123], raise_for_status=lambda: None),
            Mock(
                json=lambda: {
                    "id": 123,
                    "time": old_timestamp,
                    "title": "Old Paper",
                    "url": "https://arxiv.org/abs/2401.12345",
                    "score": 100,
                    "descendants": 10,
                },
                raise_for_status=lambda: None,
            ),
        ]

        # Fetch with 7-day window
        signals = await source.fetch_trending(time_window_hours=168, max_results=10)

        # Should be filtered out
        assert len(signals) == 0
