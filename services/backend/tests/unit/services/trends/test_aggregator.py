"""
Unit tests for TrendAggregator.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.trends.aggregator import TrendAggregator
from app.services.trends.models import TrendSignal, TrendingPaper
from app.services.trends.base import TrendSource


class MockTrendSource(TrendSource):
    """Mock trend source for testing."""

    def __init__(self, signals: list):
        super().__init__()
        self.signals = signals

    async def fetch_trending(self, topic: str = "AI", time_window_hours: int = 168, max_results: int = 50):
        return self.signals

    def extract_paper_id(self, text: str):
        return "2401.12345"


@pytest.mark.unit
class TestTrendAggregator:
    """Test suite for TrendAggregator."""

    @pytest.fixture
    def sample_signals(self):
        """Create sample trend signals."""
        return [
            TrendSignal(
                source="hackernews",
                paper_id="2401.12345",
                paper_title="Test Paper 1",
                discussion_url="https://news.ycombinator.com/item?id=123",
                timestamp=datetime.now(),
                upvotes=100,
                comments=50,
                engagement_score=40.0,
            ),
            TrendSignal(
                source="reddit",
                paper_id="2401.12345",  # Same paper
                paper_title="Test Paper 1",
                discussion_url="https://reddit.com/r/ML/123",
                timestamp=datetime.now(),
                upvotes=80,
                comments=30,
                engagement_score=35.0,
            ),
            TrendSignal(
                source="hackernews",
                paper_id="2401.67890",  # Different paper
                paper_title="Test Paper 2",
                discussion_url="https://news.ycombinator.com/item?id=456",
                timestamp=datetime.now(),
                upvotes=50,
                comments=20,
                engagement_score=25.0,
            ),
        ]

    def test_group_by_paper(self, sample_signals):
        """Test grouping signals by paper ID."""
        aggregator = TrendAggregator(sources=[])

        papers_map = aggregator._group_by_paper(sample_signals)

        assert len(papers_map) == 2
        assert len(papers_map["2401.12345"]) == 2  # Two signals for same paper
        assert len(papers_map["2401.67890"]) == 1

    def test_apply_source_weights(self, sample_signals):
        """Test applying source weights to signals."""
        aggregator = TrendAggregator(sources=[])

        source_weights = {
            "hackernews": 1.5,  # Boost HN
            "reddit": 0.5,  # Reduce Reddit
        }

        weighted_signals = aggregator._apply_source_weights(sample_signals, source_weights)

        # Check that engagement scores were weighted
        hn_signals = [s for s in weighted_signals if s.source == "hackernews"]
        reddit_signals = [s for s in weighted_signals if s.source == "reddit"]

        assert hn_signals[0].engagement_score == 40.0 * 1.5
        assert reddit_signals[0].engagement_score == 35.0 * 0.5

    def test_compute_trend_score(self, sample_signals):
        """Test trend score computation."""
        aggregator = TrendAggregator(sources=[])

        paper = TrendingPaper(
            paper_id="2401.12345",
            title="Test Paper",
            authors=["Author A"],
            summary="Test summary",
            published_date="2024-01-15",
            pdf_url="https://arxiv.org/pdf/2401.12345.pdf",
            signals=sample_signals[:2],  # Two signals
            trending_since=datetime.now(),
        )

        weights = {
            "engagement": 0.4,
            "recency": 0.3,
            "authority": 0.2,
            "velocity": 0.1,
        }

        score = aggregator._compute_trend_score(paper, weights)

        # Score should be between 0 and 100
        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_generate_trending_reasons(self, sample_signals):
        """Test generation of trending reasons."""
        aggregator = TrendAggregator(sources=[])

        paper = TrendingPaper(
            paper_id="2401.12345",
            title="Test Paper",
            authors=[],
            summary="",
            published_date="",
            pdf_url="",
            total_mentions=2,
            total_engagement=280,
            buzz_velocity=1.5,
            signals=sample_signals[:2],
        )

        reasons = aggregator._generate_trending_reasons(paper)

        assert len(reasons) > 0
        assert any("280 total interactions" in r for r in reasons)
        assert any("100 points on HackerNews" in r for r in reasons)

    @pytest.mark.asyncio
    async def test_fetch_all_sources(self, sample_signals):
        """Test fetching from all sources in parallel."""
        # Create mock sources
        source1 = MockTrendSource([sample_signals[0]])
        source2 = MockTrendSource([sample_signals[1]])

        aggregator = TrendAggregator(sources=[source1, source2])

        all_signals = await aggregator._fetch_all_sources(topic="AI", time_window_hours=168)

        assert len(all_signals) == 2
        assert all_signals[0].paper_id == "2401.12345"
        assert all_signals[1].paper_id == "2401.12345"

    @pytest.mark.asyncio
    async def test_fetch_all_sources_handles_errors(self):
        """Test that errors from one source don't break aggregation."""
        # Create a mock source that raises an error
        error_source = Mock()
        error_source.fetch_trending = AsyncMock(side_effect=Exception("API Error"))

        # And a working source
        working_signal = TrendSignal(
            source="hackernews",
            paper_id="2401.12345",
            paper_title="Working Paper",
            discussion_url="https://example.com",
            timestamp=datetime.now(),
        )
        working_source = MockTrendSource([working_signal])

        aggregator = TrendAggregator(sources=[error_source, working_source])

        # Should still work with the working source
        all_signals = await aggregator._fetch_all_sources(topic="AI", time_window_hours=168)

        assert len(all_signals) == 1
        assert all_signals[0].paper_id == "2401.12345"

    @pytest.mark.asyncio
    @patch("app.services.trends.aggregator.ArxivService")
    async def test_enrich_with_arxiv_data(self, mock_arxiv_service_class, sample_signals):
        """Test enriching with arXiv metadata."""
        # Setup mock arXiv service
        mock_arxiv_service = Mock()
        mock_arxiv_service.search_papers.return_value = [
            {
                "id": "2401.12345",
                "title": "Full Paper Title from arXiv",
                "authors": ["Author A", "Author B"],
                "summary": "Detailed summary from arXiv...",
                "published_date": datetime(2024, 1, 15),
                "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
            }
        ]

        aggregator = TrendAggregator(sources=[], arxiv_service=mock_arxiv_service)

        papers_map = {"2401.12345": sample_signals[:2]}

        trending_papers = await aggregator._enrich_with_arxiv_data(papers_map)

        assert len(trending_papers) == 1
        paper = trending_papers[0]

        assert paper.title == "Full Paper Title from arXiv"
        assert len(paper.authors) == 2
        assert paper.total_mentions == 2
        assert len(paper.sources) == 2  # hackernews and reddit

    @pytest.mark.asyncio
    @patch("app.services.trends.aggregator.ArxivService")
    async def test_discover_trending_papers_end_to_end(self, mock_arxiv_service_class, sample_signals):
        """Test complete discovery flow."""
        # Setup mock arXiv service
        mock_arxiv_service = Mock()
        mock_arxiv_service.search_papers.return_value = [
            {
                "id": "2401.12345",
                "title": "Trending Paper",
                "authors": ["Author A"],
                "summary": "Summary...",
                "published_date": datetime(2024, 1, 15),
                "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
            }
        ]

        # Create mock source
        source = MockTrendSource(sample_signals)

        aggregator = TrendAggregator(sources=[source], arxiv_service=mock_arxiv_service)

        # Execute discovery
        trending_papers = await aggregator.discover_trending_papers(
            topic="AI", time_window_hours=168, max_results=10
        )

        # Should have deduplicated and ranked papers
        assert len(trending_papers) > 0
        assert all(hasattr(p, "trend_score") for p in trending_papers)
        assert all(len(p.trending_reasons) > 0 for p in trending_papers)

        # Papers should be sorted by trend score
        if len(trending_papers) > 1:
            assert trending_papers[0].trend_score >= trending_papers[1].trend_score
