# HackerNews Trend Source - Implementation Guide

## Overview

HackerNews is the **ideal first source** for trend discovery because:
- ✅ Completely free, no API key required
- ✅ Simple REST API with excellent documentation
- ✅ High-quality technical discussions
- ✅ Strong ML/AI community presence
- ✅ Papers frequently shared and discussed

## HackerNews API Basics

### Base URL
```
https://hacker-news.firebaseio.com/v0/
```

### Key Endpoints

1. **Get Top Stories**
   ```
   GET /topstories.json
   Returns: [story_id1, story_id2, ...]  (up to 500 IDs)
   ```

2. **Get Best Stories**
   ```
   GET /beststories.json
   Returns: [story_id1, story_id2, ...]
   ```

3. **Get Story Details**
   ```
   GET /item/{story_id}.json
   Returns: {
     "id": 12345,
     "type": "story",
     "by": "username",
     "time": 1234567890,
     "title": "Paper Title",
     "url": "https://arxiv.org/abs/2401.12345",
     "score": 150,
     "descendants": 42  // comment count
   }
   ```

## Implementation Strategy

### Step 1: Detect arXiv Papers

Search for stories containing:
- **URL matches**: `arxiv.org/abs/`, `arxiv.org/pdf/`
- **Title keywords**: "arxiv:", "[2401.12345]"
- **Domain**: `arxiv.org` in URL field

### Step 2: Extract Paper IDs

From various formats:
```
https://arxiv.org/abs/2401.12345
https://arxiv.org/abs/2401.12345v2
https://arxiv.org/pdf/2401.12345.pdf
arxiv:2401.12345
[2401.12345]
```

Regex pattern:
```python
r'(?:arxiv\.org/(?:abs|pdf)/|arxiv:|\[)?(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf|\])?'
```

### Step 3: Compute Engagement Score

```python
engagement_score = (
    story["score"] +              # Upvotes
    story["descendants"] * 2      # Comments (weighted 2x)
)
```

### Step 4: Extract Context

Fetch top comments to understand WHY it's trending:
```
GET /item/{story_id}.json  -> get "kids" (comment IDs)
GET /item/{comment_id}.json  -> get comment text
```

---

## Code Implementation

### File Structure

```
services/backend/app/services/trends/
├── __init__.py
├── base.py                    # TrendSource abstract class
├── models.py                  # TrendSignal, TrendingPaper
├── aggregator.py              # TrendAggregator
├── sources/
│   ├── __init__.py
│   ├── hackernews.py         # HackerNewsSource
│   ├── reddit.py             # RedditSource (future)
│   └── paperwithcode.py      # PapersWithCodeSource (future)
└── utils.py                   # Paper ID extraction, caching
```

### models.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict

@dataclass
class TrendSignal:
    """A single mention/discussion of a paper on a platform."""
    source: str              # "hackernews", "reddit", etc.
    paper_id: str            # arXiv ID (e.g., "2401.12345")
    paper_title: str
    discussion_url: str      # Link to the discussion
    timestamp: datetime

    # Engagement metrics
    upvotes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0

    # Computed
    engagement_score: float = 0.0

    # Context
    discussion_snippet: str = ""
    author: str = ""
    author_credibility: float = 0.5  # 0-1 score

    # Source-specific metadata
    metadata: Dict = field(default_factory=dict)


@dataclass
class TrendingPaper:
    """A paper with aggregated trend data from multiple sources."""
    paper_id: str
    title: str
    authors: List[str]
    summary: str
    published_date: str
    pdf_url: str

    # Trend metrics
    trend_score: float = 0.0
    total_mentions: int = 0
    total_engagement: int = 0
    trending_since: datetime = None
    buzz_velocity: float = 0.0  # Mentions per day

    # Source breakdown
    sources: List[str] = field(default_factory=list)
    signals: List[TrendSignal] = field(default_factory=list)

    # Discussion context
    top_discussion_snippet: str = ""
    discussion_urls: List[str] = field(default_factory=list)
```

### base.py

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timedelta
import re

from .models import TrendSignal

class TrendSource(ABC):
    """Abstract base class for trend sources."""

    def __init__(self, cache_ttl: int = 3600):
        """
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}

    @abstractmethod
    async def fetch_trending(
        self,
        topic: str = "AI",
        time_window_hours: int = 168,
        max_results: int = 50
    ) -> List[TrendSignal]:
        """
        Fetch trending papers from this source.

        Args:
            topic: Topic to search for (e.g., "AI", "LLM", "ML")
            time_window_hours: How far back to look (default: 1 week)
            max_results: Maximum number of signals to return

        Returns:
            List of TrendSignal objects
        """
        pass

    @abstractmethod
    def extract_paper_id(self, text: str) -> Optional[str]:
        """
        Extract arXiv paper ID from URL or text.

        Args:
            text: URL or text containing arXiv reference

        Returns:
            arXiv ID (e.g., "2401.12345") or None
        """
        pass

    def compute_engagement_score(self, signal: TrendSignal) -> float:
        """
        Compute normalized engagement score for a signal.

        Default formula: upvotes + (comments * 2) + (shares * 3)
        Can be overridden by subclasses for platform-specific scoring.

        Args:
            signal: TrendSignal object

        Returns:
            Engagement score (0-100)
        """
        raw_score = (
            signal.upvotes +
            (signal.comments * 2) +
            (signal.shares * 3)
        )
        # Normalize to 0-100 scale (adjust divisor based on platform)
        return min(100, raw_score / 10)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache_timestamps:
            return False

        age = (datetime.now() - self._cache_timestamps[cache_key]).seconds
        return age < self.cache_ttl

    def _get_from_cache(self, cache_key: str) -> Optional[List[TrendSignal]]:
        """Get data from cache if valid."""
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def _save_to_cache(self, cache_key: str, data: List[TrendSignal]):
        """Save data to cache."""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()
```

### sources/hackernews.py

```python
import httpx
import re
from typing import List, Optional
from datetime import datetime, timedelta

from ..base import TrendSource
from ..models import TrendSignal

class HackerNewsSource(TrendSource):
    """Fetch trending papers from HackerNews."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    ARXIV_PATTERNS = [
        r'arxiv\.org/abs/(\d{4}\.\d{4,5})',
        r'arxiv\.org/pdf/(\d{4}\.\d{4,5})',
        r'arxiv:(\d{4}\.\d{4,5})',
        r'\[(\d{4}\.\d{4,5})\]',
    ]

    async def fetch_trending(
        self,
        topic: str = "AI",
        time_window_hours: int = 168,
        max_results: int = 50
    ) -> List[TrendSignal]:
        """
        Fetch trending arXiv papers from HackerNews.

        Strategy:
        1. Get top stories from HN
        2. Filter for arXiv links
        3. Extract paper IDs and engagement metrics
        4. Return as TrendSignal objects
        """

        # Check cache first
        cache_key = f"hn_{topic}_{time_window_hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        signals = []
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        async with httpx.AsyncClient() as client:
            # Fetch top story IDs
            response = await client.get(f"{self.BASE_URL}/topstories.json")
            story_ids = response.json()[:200]  # Check top 200 stories

            # Fetch story details in batches
            for story_id in story_ids[:max_results * 2]:  # Overfetch to account for filtering
                story = await self._get_story(client, story_id)

                if not story:
                    continue

                # Check if story is within time window
                story_time = datetime.fromtimestamp(story["time"])
                if story_time < cutoff_time:
                    continue

                # Check if story contains arXiv link
                paper_id = self._extract_paper_from_story(story)
                if not paper_id:
                    continue

                # Check if topic matches (if specific topic requested)
                if topic and topic.lower() != "ai":
                    if not self._matches_topic(story, topic):
                        continue

                # Create TrendSignal
                signal = TrendSignal(
                    source="hackernews",
                    paper_id=paper_id,
                    paper_title=story.get("title", ""),
                    discussion_url=f"https://news.ycombinator.com/item?id={story_id}",
                    timestamp=story_time,
                    upvotes=story.get("score", 0),
                    comments=story.get("descendants", 0),
                    author=story.get("by", ""),
                    metadata={
                        "hn_id": story_id,
                        "hn_url": story.get("url", ""),
                    }
                )

                # Compute engagement score
                signal.engagement_score = self.compute_engagement_score(signal)

                # Optionally fetch top comment for context
                if story.get("kids"):
                    top_comment = await self._get_top_comment(client, story["kids"])
                    if top_comment:
                        signal.discussion_snippet = top_comment

                signals.append(signal)

                if len(signals) >= max_results:
                    break

        # Save to cache
        self._save_to_cache(cache_key, signals)

        return signals

    async def _get_story(self, client: httpx.AsyncClient, story_id: int) -> Optional[dict]:
        """Fetch story details from HN API."""
        try:
            response = await client.get(f"{self.BASE_URL}/item/{story_id}.json")
            return response.json()
        except Exception as e:
            print(f"Error fetching story {story_id}: {e}")
            return None

    async def _get_top_comment(self, client: httpx.AsyncClient, comment_ids: List[int]) -> Optional[str]:
        """Fetch the first comment for context."""
        if not comment_ids:
            return None

        try:
            first_comment_id = comment_ids[0]
            response = await client.get(f"{self.BASE_URL}/item/{first_comment_id}.json")
            comment = response.json()
            return comment.get("text", "")[:200]  # First 200 chars
        except Exception:
            return None

    def _extract_paper_from_story(self, story: dict) -> Optional[str]:
        """Extract arXiv paper ID from HN story."""
        # Check URL field
        url = story.get("url", "")
        paper_id = self.extract_paper_id(url)
        if paper_id:
            return paper_id

        # Check title
        title = story.get("title", "")
        paper_id = self.extract_paper_id(title)
        return paper_id

    def extract_paper_id(self, text: str) -> Optional[str]:
        """Extract arXiv ID from text using multiple patterns."""
        for pattern in self.ARXIV_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _matches_topic(self, story: dict, topic: str) -> bool:
        """Check if story matches the requested topic."""
        text = f"{story.get('title', '')} {story.get('url', '')}".lower()

        # Topic keyword mapping
        topic_keywords = {
            "llm": ["llm", "language model", "gpt", "transformer"],
            "genai": ["generative", "generation", "diffusion", "gan"],
            "ml": ["machine learning", "deep learning", "neural"],
            "cv": ["computer vision", "image", "vision"],
            "nlp": ["nlp", "natural language", "text"],
        }

        keywords = topic_keywords.get(topic.lower(), [topic.lower()])
        return any(keyword in text for keyword in keywords)

    def compute_engagement_score(self, signal: TrendSignal) -> float:
        """
        HackerNews-specific engagement scoring.

        HN points are valuable, comments indicate high interest.
        Typical ranges:
        - Front page: 100-500 points
        - Top post: 500-2000 points
        - Viral: 2000+ points
        """
        raw_score = signal.upvotes + (signal.comments * 2)

        # Normalize to 0-100
        # 500 points = 100 score (top story)
        return min(100, (raw_score / 500) * 100)
```

### aggregator.py

```python
import asyncio
from typing import List, Dict
from datetime import datetime
from collections import defaultdict
import math

from .base import TrendSource
from .models import TrendSignal, TrendingPaper
from app.services.arxiv_service import ArxivService

class TrendAggregator:
    """Aggregate trend signals from multiple sources."""

    def __init__(self, sources: List[TrendSource], arxiv_service: ArxivService = None):
        self.sources = sources
        self.arxiv_service = arxiv_service or ArxivService()

    async def discover_trending_papers(
        self,
        topic: str = "AI",
        time_window_hours: int = 168,
        max_results: int = 20
    ) -> List[TrendingPaper]:
        """
        Discover trending papers by aggregating signals from all sources.

        Steps:
        1. Fetch signals from all sources (parallel)
        2. Group signals by paper ID
        3. Fetch paper metadata from arXiv
        4. Compute trend scores
        5. Rank and return top papers
        """

        # Step 1: Fetch from all sources concurrently
        signals = await self._fetch_all_sources(topic, time_window_hours)

        if not signals:
            return []

        # Step 2: Group by paper ID
        papers_map = self._group_by_paper(signals)

        # Step 3: Fetch arXiv metadata for each paper
        trending_papers = await self._enrich_with_arxiv_data(papers_map)

        # Step 4: Compute trend scores
        for paper in trending_papers:
            paper.trend_score = self._compute_trend_score(paper)

        # Step 5: Rank by trend score
        trending_papers.sort(key=lambda p: p.trend_score, reverse=True)

        return trending_papers[:max_results]

    async def _fetch_all_sources(
        self,
        topic: str,
        time_window_hours: int
    ) -> List[TrendSignal]:
        """Fetch signals from all sources in parallel."""
        tasks = [
            source.fetch_trending(topic, time_window_hours)
            for source in self.sources
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and filter out errors
        all_signals = []
        for result in results:
            if isinstance(result, list):
                all_signals.extend(result)
            else:
                print(f"Error fetching from source: {result}")

        return all_signals

    def _group_by_paper(self, signals: List[TrendSignal]) -> Dict[str, List[TrendSignal]]:
        """Group signals by paper ID."""
        papers_map = defaultdict(list)
        for signal in signals:
            papers_map[signal.paper_id].append(signal)
        return papers_map

    async def _enrich_with_arxiv_data(
        self,
        papers_map: Dict[str, List[TrendSignal]]
    ) -> List[TrendingPaper]:
        """Fetch full paper metadata from arXiv for each trending paper."""
        trending_papers = []

        for paper_id, signals in papers_map.items():
            # Fetch from arXiv
            papers_data = self.arxiv_service.search_papers(query=paper_id, max_results=1)

            if not papers_data:
                # If arXiv fetch fails, use data from signals
                paper_data = {
                    "id": paper_id,
                    "title": signals[0].paper_title,
                    "authors": [],
                    "summary": "",
                    "published_date": datetime.now(),
                    "pdf_url": f"https://arxiv.org/pdf/{paper_id}.pdf",
                }
            else:
                paper_data = papers_data[0]

            # Create TrendingPaper
            trending_paper = TrendingPaper(
                paper_id=paper_id,
                title=paper_data["title"],
                authors=paper_data.get("authors", []),
                summary=paper_data.get("summary", ""),
                published_date=str(paper_data.get("published_date", "")),
                pdf_url=paper_data["pdf_url"],
                total_mentions=len(signals),
                total_engagement=sum(s.upvotes + s.comments for s in signals),
                trending_since=min(s.timestamp for s in signals),
                sources=list(set(s.source for s in signals)),
                signals=signals,
                discussion_urls=[s.discussion_url for s in signals],
            )

            # Set top discussion snippet (most upvoted)
            top_signal = max(signals, key=lambda s: s.engagement_score)
            trending_paper.top_discussion_snippet = top_signal.discussion_snippet

            # Compute buzz velocity (mentions per day)
            age_days = (datetime.now() - trending_paper.trending_since).days or 1
            trending_paper.buzz_velocity = len(signals) / age_days

            trending_papers.append(trending_paper)

        return trending_papers

    def _compute_trend_score(self, paper: TrendingPaper) -> float:
        """
        Compute multi-factor trend score.

        Score = (0.5 × Engagement) + (0.3 × Recency) + (0.2 × Authority)

        Returns:
            Score from 0-100
        """

        # 1. Engagement component (0-100)
        total_engagement = sum(
            s.upvotes + (s.comments * 2) + (s.shares * 3)
            for s in paper.signals
        )
        engagement_score = min(100, total_engagement / 10)

        # 2. Recency component (0-100)
        # Use exponential decay: older = lower score
        age_days = (datetime.now() - paper.trending_since).days
        recency_score = 100 * math.exp(-age_days / 7)  # 7-day half-life

        # 3. Authority component (0-100)
        # Average credibility of authors/discussants
        if paper.signals:
            authority_score = 100 * sum(s.author_credibility for s in paper.signals) / len(paper.signals)
        else:
            authority_score = 50

        # 4. Buzz velocity bonus (0-20)
        # Papers gaining traction quickly get a boost
        velocity_bonus = min(20, paper.buzz_velocity * 5)

        # Weighted combination
        trend_score = (
            0.4 * engagement_score +
            0.3 * recency_score +
            0.2 * authority_score +
            0.1 * velocity_bonus
        )

        return round(trend_score, 2)
```

---

## API Endpoint Implementation

### routers/v1/trends.py

```python
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.services.trends.aggregator import TrendAggregator
from app.services.trends.sources.hackernews import HackerNewsSource
from app.services.arxiv_service import ArxivService

router = APIRouter(prefix="/api/v1/trends", tags=["trends"])

class TrendingPaperResponse(BaseModel):
    id: str
    title: str
    authors: List[str]
    summary: str
    published_date: str
    pdf_url: str
    trend_score: float
    total_mentions: int
    total_engagement: int
    buzz_velocity: float
    sources: List[str]
    discussion_urls: List[str]
    top_discussion_snippet: str

class TrendDiscoveryResponse(BaseModel):
    papers: List[TrendingPaperResponse]
    metadata: dict

@router.get("/discover", response_model=TrendDiscoveryResponse)
async def discover_trending_papers(
    topic: str = Query("AI", description="Topic to search for"),
    time_window: int = Query(168, description="Time window in hours", ge=1, le=720),
    max_results: int = Query(20, description="Maximum results", ge=1, le=100),
):
    """
    Discover trending papers based on social media buzz.

    Currently supports: HackerNews
    Future: Reddit, Twitter, Papers with Code, etc.
    """

    try:
        # Initialize aggregator with sources
        aggregator = TrendAggregator(
            sources=[HackerNewsSource()],
            arxiv_service=ArxivService()
        )

        # Discover trending papers
        trending_papers = await aggregator.discover_trending_papers(
            topic=topic,
            time_window_hours=time_window,
            max_results=max_results
        )

        # Convert to response model
        papers_response = [
            TrendingPaperResponse(
                id=p.paper_id,
                title=p.title,
                authors=p.authors,
                summary=p.summary,
                published_date=p.published_date,
                pdf_url=p.pdf_url,
                trend_score=p.trend_score,
                total_mentions=p.total_mentions,
                total_engagement=p.total_engagement,
                buzz_velocity=p.buzz_velocity,
                sources=p.sources,
                discussion_urls=p.discussion_urls,
                top_discussion_snippet=p.top_discussion_snippet,
            )
            for p in trending_papers
        ]

        return TrendDiscoveryResponse(
            papers=papers_response,
            metadata={
                "sources_queried": ["hackernews"],
                "total_papers_found": len(papers_response),
                "time_window_hours": time_window,
                "topic": topic,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering trends: {str(e)}")

@router.get("/hackernews", response_model=List[TrendingPaperResponse])
async def get_hackernews_trends(
    time_window: int = Query(168, ge=1, le=720),
    max_results: int = Query(20, ge=1, le=100),
):
    """Get trending papers specifically from HackerNews."""

    source = HackerNewsSource()
    signals = await source.fetch_trending(time_window_hours=time_window, max_results=max_results)

    # Convert to response (simplified without arXiv enrichment)
    return [
        TrendingPaperResponse(
            id=s.paper_id,
            title=s.paper_title,
            authors=[],
            summary="",
            published_date="",
            pdf_url=f"https://arxiv.org/pdf/{s.paper_id}.pdf",
            trend_score=s.engagement_score,
            total_mentions=1,
            total_engagement=s.upvotes + s.comments,
            buzz_velocity=0,
            sources=["hackernews"],
            discussion_urls=[s.discussion_url],
            top_discussion_snippet=s.discussion_snippet,
        )
        for s in signals
    ]
```

---

## Testing

### tests/unit/services/trends/test_hackernews.py

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.trends.sources.hackernews import HackerNewsSource

@pytest.mark.unit
class TestHackerNewsSource:

    @pytest.fixture
    def source(self):
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

    def test_extract_paper_id_from_title(self, source):
        """Test extracting paper ID from title with brackets."""
        title = "New LLM Paper [2401.12345]"
        paper_id = source.extract_paper_id(title)
        assert paper_id == "2401.12345"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_trending(self, mock_client_class, source):
        """Test fetching trending papers from HackerNews."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock top stories response
        mock_client.get.side_effect = [
            # First call: get top stories
            Mock(json=lambda: [123, 456]),
            # Second call: story 123
            Mock(json=lambda: {
                "id": 123,
                "type": "story",
                "by": "user1",
                "time": int(datetime.now().timestamp()),
                "title": "Interesting AI Paper",
                "url": "https://arxiv.org/abs/2401.12345",
                "score": 150,
                "descendants": 42,
            }),
            # Third call: story 456
            Mock(json=lambda: {
                "id": 456,
                "type": "story",
                "by": "user2",
                "time": int(datetime.now().timestamp()),
                "title": "Another Paper",
                "url": "https://example.com",
                "score": 100,
                "descendants": 10,
            }),
        ]

        # Execute
        signals = await source.fetch_trending(max_results=10)

        # Assert
        assert len(signals) >= 1
        assert signals[0].paper_id == "2401.12345"
        assert signals[0].source == "hackernews"
        assert signals[0].upvotes == 150
        assert signals[0].comments == 42
```

---

## Usage Examples

### Example 1: Discover Trending Papers

```bash
curl "http://localhost:8000/api/v1/trends/discover?topic=LLM&time_window=168"
```

Response:
```json
{
  "papers": [
    {
      "id": "2401.12345",
      "title": "Constitutional AI: Harmlessness from AI Feedback",
      "trend_score": 87.5,
      "total_mentions": 3,
      "sources": ["hackernews"],
      "discussion_urls": [
        "https://news.ycombinator.com/item?id=123456"
      ],
      "top_discussion_snippet": "This is a game-changer for alignment..."
    }
  ],
  "metadata": {
    "sources_queried": ["hackernews"],
    "total_papers_found": 15,
    "time_window_hours": 168
  }
}
```

### Example 2: HackerNews Only

```bash
curl "http://localhost:8000/api/v1/trends/hackernews?time_window=72"
```

---

## Next Steps

1. ✅ Review this implementation guide
2. Create the file structure in `app/services/trends/`
3. Implement `HackerNewsSource` first
4. Add unit tests
5. Test with real HackerNews API
6. Integrate with frontend
7. Monitor performance and iterate

Ready to start implementing?
