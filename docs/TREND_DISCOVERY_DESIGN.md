# Trend Discovery Feature - Design Document

## Overview

Enhance the agentic research discovery system to identify trending GenAI/LLM papers based on social media buzz, expert discussions, and community engagement across multiple platforms.

**Goal**: Learn about cutting-edge trends by discovering what AI researchers, practitioners, and enthusiasts are actively discussing and building.

---

## Requirements

### Functional Requirements
1. ✅ Discover papers getting significant buzz on social platforms
2. ✅ Aggregate signals from multiple sources (Twitter/X, HackerNews, Reddit, GitHub, etc.)
3. ✅ Rank papers by combined "trend score" (engagement + recency + authority)
4. ✅ Extensible architecture to add new sources easily
5. ✅ Cache results to avoid redundant API calls
6. ✅ Integrate with existing researcher agent

### Non-Functional Requirements
1. ✅ Free or low-cost implementation (start with free APIs)
2. ✅ Fast response times (<5s for trend discovery)
3. ✅ Respect API rate limits
4. ✅ Graceful degradation if a source is unavailable
5. ✅ Testable and maintainable code

---

## Source Analysis

### Tier 1: Easiest & Free (Start Here)

| Source | Pros | Cons | Effort | API Cost |
|--------|------|------|--------|----------|
| **HackerNews** | ✅ Free API<br>✅ No auth required<br>✅ High-quality ML discussions<br>✅ Simple REST API | ❌ Lower volume than Twitter<br>❌ Tech-focused audience only | **Low** | **FREE** |
| **Reddit** | ✅ Free tier (100 req/min)<br>✅ Multiple ML subreddits<br>✅ Good discussions | ❌ Requires OAuth<br>❌ Rate limits<br>❌ More noise | **Medium** | **FREE** |
| **arXiv Sanity Lite** | ✅ Free<br>✅ Papers already ranked<br>✅ Simple scraping | ❌ May need scraping<br>❌ Limited metadata | **Low** | **FREE** |

### Tier 2: High Value (Add Later)

| Source | Pros | Cons | Effort | API Cost |
|--------|------|------|--------|----------|
| **Papers with Code** | ✅ Free API<br>✅ GitHub stars tracking<br>✅ Implementation counts | ❌ Not all papers included<br>❌ Delayed updates | **Medium** | **FREE** |
| **Hugging Face** | ✅ Trending models API<br>✅ Download metrics<br>✅ Links to papers | ❌ Model-centric, not paper-centric | **Medium** | **FREE** |
| **Semantic Scholar** | ✅ Citation velocity<br>✅ Influence metrics<br>✅ Free API | ❌ Rate limits<br>❌ Requires API key | **Medium** | **FREE** |

### Tier 3: Premium (Future)

| Source | Pros | Cons | Effort | API Cost |
|--------|------|------|--------|----------|
| **Twitter/X** | ✅ Real-time trends<br>✅ Expert opinions<br>✅ Viral spread | ❌ **Expensive API** ($100+/mo)<br>❌ Complex auth | **High** | **$$$** |
| **Google Scholar** | ✅ Citation metrics<br>✅ Comprehensive | ❌ No official API<br>❌ Scraping ToS violations | **High** | **N/A** |

---

## Recommended Sources (Phase 1)

### 1. HackerNews (PRIMARY - Start Here)
- **Why**: Completely free, no auth, excellent signal-to-noise ratio
- **What to track**: Stories mentioning arXiv links, upvotes, comment count
- **API**: https://github.com/HackerNews/API
- **Example**: Search for "arxiv.org" in story URLs/text, rank by points + comments

### 2. Reddit (SECONDARY)
- **Subreddits**: r/MachineLearning, r/LocalLLaMA, r/LanguageTechnology, r/MLQuestions
- **Why**: Active AI community, good discussions
- **What to track**: Posts with arXiv links, upvotes, comment engagement
- **API**: PRAW (Python Reddit API Wrapper)

### 3. arXiv Stats (TERTIARY)
- **Why**: Official arXiv download/view counts (if available)
- **What to track**: Most downloaded papers in cs.AI, cs.LG, cs.CL categories
- **API**: No official API, but RSS feeds available

---

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Researcher Agent                        │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │         Trend Discovery Module                  │    │
│  │  ┌──────────────────────────────────────────┐  │    │
│  │  │      TrendAggregator                     │  │    │
│  │  │  - Fetches from all sources              │  │    │
│  │  │  - Deduplicates papers                   │  │    │
│  │  │  - Computes trend scores                 │  │    │
│  │  └──────────────────────────────────────────┘  │    │
│  │              ▲                                  │    │
│  │              │ aggregates                       │    │
│  │              │                                  │    │
│  │  ┌───────────┴──────────────────────────────┐  │    │
│  │  │         TrendSource (Abstract)           │  │    │
│  │  │  - fetch_trending()                      │  │    │
│  │  │  - extract_papers()                      │  │    │
│  │  │  - compute_score()                       │  │    │
│  │  └──────────────────────────────────────────┘  │    │
│  │              △                                  │    │
│  │              │ implements                       │    │
│  │     ┌────────┼────────┬──────────┐             │    │
│  │     │        │        │          │             │    │
│  │  ┌──▽──┐ ┌──▽──┐ ┌───▽──┐ ┌────▽───┐          │    │
│  │  │ HN  │ │Reddit│ │Papers│ │Twitter │          │    │
│  │  │Source│ │Source│ │w/Code│ │Source │          │    │
│  │  └─────┘ └─────┘ └──────┘ └────────┘          │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Traditional ArXiv Search                                │
│  + Trend-Boosted Results                                 │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. TrendSource (Abstract Base Class)

```python
class TrendSource(ABC):
    """Abstract base class for trend sources."""

    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self.cache = {}

    @abstractmethod
    async def fetch_trending(self, topic: str = "AI") -> List[TrendSignal]:
        """Fetch trending discussions/mentions."""
        pass

    @abstractmethod
    def extract_paper_id(self, url: str) -> Optional[str]:
        """Extract arXiv ID from URL or text."""
        pass

    def compute_engagement_score(self, signal: TrendSignal) -> float:
        """Compute engagement score for a signal."""
        pass
```

#### 2. TrendSignal (Data Class)

```python
@dataclass
class TrendSignal:
    """Represents a single trending mention of a paper."""
    source: str              # "hackernews", "reddit", etc.
    paper_id: str            # arXiv ID
    paper_title: str
    url: str                 # Link to discussion
    engagement_score: float  # Normalized 0-100
    timestamp: datetime
    metadata: dict           # Source-specific data

    # Engagement metrics
    upvotes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0

    # Context
    discussion_snippet: str = ""
    author_credibility: float = 0.0  # 0-1 score
```

#### 3. HackerNewsSource (Implementation)

```python
class HackerNewsSource(TrendSource):
    """Fetch trending papers from HackerNews."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    async def fetch_trending(self, topic: str = "AI") -> List[TrendSignal]:
        """
        1. Fetch top/best stories
        2. Filter for arXiv links or AI keywords
        3. Extract paper IDs
        4. Compute engagement scores
        """
        pass

    def extract_paper_id(self, url: str) -> Optional[str]:
        """Extract arXiv ID from HN story URL."""
        # Match patterns: arxiv.org/abs/2401.12345
        pass

    async def get_story_details(self, story_id: int) -> dict:
        """Fetch story metadata (points, comments)."""
        pass
```

#### 4. TrendAggregator (Orchestrator)

```python
class TrendAggregator:
    """Aggregate trend signals from multiple sources."""

    def __init__(self, sources: List[TrendSource]):
        self.sources = sources

    async def discover_trending_papers(
        self,
        topic: str = "AI",
        max_results: int = 20,
        time_window_hours: int = 168  # 1 week
    ) -> List[TrendingPaper]:
        """
        1. Fetch signals from all sources in parallel
        2. Deduplicate by paper ID
        3. Aggregate engagement scores
        4. Rank by combined trend score
        5. Return top N papers
        """

        # Fetch from all sources concurrently
        signals = await self._fetch_all_sources(topic)

        # Group by paper ID
        papers_map = self._group_by_paper(signals)

        # Compute trend scores
        trending_papers = self._compute_trend_scores(papers_map)

        # Rank and return
        return sorted(trending_papers, key=lambda p: p.trend_score, reverse=True)[:max_results]

    def _compute_trend_score(self, paper: TrendingPaper) -> float:
        """
        Trend Score = (Engagement × Recency × Authority)

        Engagement = Σ(upvotes + comments×2 + shares×3)
        Recency = exp(-age_in_days / decay_factor)
        Authority = avg(author_credibility_scores)
        """
        pass
```

#### 5. TrendingPaper (Output Model)

```python
@dataclass
class TrendingPaper:
    """A paper with aggregated trend data."""
    paper_id: str
    title: str
    authors: List[str]
    summary: str
    published_date: datetime
    pdf_url: str

    # Trend metrics
    trend_score: float          # Combined 0-100
    total_mentions: int         # Across all sources
    total_engagement: int       # Sum of all interactions
    trending_since: datetime    # First mention timestamp
    buzz_velocity: float        # Mentions per day

    # Source breakdown
    sources: List[str]          # ["hackernews", "reddit"]
    signals: List[TrendSignal]  # Individual mentions

    # Context
    top_discussion_snippet: str  # Most upvoted comment
    discussion_urls: List[str]   # Links to discussions
```

---

## Scoring Algorithm

### Trend Score Formula

```python
def compute_trend_score(paper: TrendingPaper) -> float:
    """
    Multi-factor scoring:

    Score = (0.5 × Engagement) + (0.3 × Recency) + (0.2 × Authority)

    Where:
    - Engagement = normalized (upvotes + comments×2 + shares×3)
    - Recency = exp(-days_since_first_mention / 7)  # 7-day decay
    - Authority = avg credibility of discussants
    """

    # Engagement component (0-100)
    engagement = sum(
        s.upvotes + s.comments * 2 + s.shares * 3
        for s in paper.signals
    )
    engagement_score = min(100, engagement / 10)  # Normalize

    # Recency component (0-100)
    age_days = (datetime.now() - paper.trending_since).days
    recency_score = 100 * math.exp(-age_days / 7)  # 7-day half-life

    # Authority component (0-100)
    if paper.signals:
        authority_score = 100 * sum(s.author_credibility for s in paper.signals) / len(paper.signals)
    else:
        authority_score = 50  # Default

    # Weighted combination
    trend_score = (
        0.5 * engagement_score +
        0.3 * recency_score +
        0.2 * authority_score
    )

    return round(trend_score, 2)
```

### Engagement Scoring

Different platforms have different scales:

| Platform | Metric | Weight | Normalization |
|----------|--------|--------|---------------|
| HackerNews | Points | 1.0 | points / 10 |
| HackerNews | Comments | 2.0 | comments / 5 |
| Reddit | Upvotes | 1.0 | upvotes / 100 |
| Reddit | Comments | 2.0 | comments / 10 |
| Twitter | Likes | 0.5 | likes / 1000 |
| Twitter | Retweets | 3.0 | retweets / 100 |
| GitHub | Stars | 2.0 | stars / 50 |

---

## Integration with Researcher Agent

### Current Flow (Existing)
```
User Query → Generate Search Terms → ArXiv Search → Return Papers
```

### New Flow (Enhanced)
```
User Query
    ↓
    ├─→ Traditional Search (ArXiv)
    └─→ Trend Discovery (Social Buzz)
    ↓
Merge & Rank (Relevance + Trend Score)
    ↓
Return Hybrid Results
```

### LangGraph Node Addition

Add a new node to the researcher agent:

```python
async def discover_trending_node(state: ResearchState) -> ResearchState:
    """
    Node: Discover trending papers based on social buzz.

    Input: user_context, user_query
    Output: trending_papers (List[TrendingPaper])
    """
    aggregator = TrendAggregator(sources=[
        HackerNewsSource(),
        RedditSource(),
    ])

    # Extract topic from query or use default
    topic = extract_topic(state.get("user_query", "")) or "AI"

    # Discover trending papers
    trending_papers = await aggregator.discover_trending_papers(
        topic=topic,
        max_results=10,
        time_window_hours=168  # 1 week
    )

    # Convert to standard paper format
    papers_data = [
        {
            "id": p.paper_id,
            "title": p.title,
            "authors": p.authors,
            "summary": p.summary,
            "published_date": p.published_date,
            "pdf_url": p.pdf_url,
            "trend_score": p.trend_score,  # Additional metadata
            "total_mentions": p.total_mentions,
            "discussion_urls": p.discussion_urls,
        }
        for p in trending_papers
    ]

    state["trending_papers"] = papers_data
    return state
```

---

## Implementation Phases

### Phase 1: HackerNews Integration (Week 1)
**Goal**: Prove concept with single source

- [ ] Create `app/services/trends/` directory
- [ ] Implement `TrendSource` abstract base class
- [ ] Implement `HackerNewsSource`
- [ ] Add basic caching layer
- [ ] Add unit tests
- [ ] Create `/api/v1/trends/hackernews` endpoint
- [ ] Test with frontend

**Deliverables**:
- Working HackerNews trend discovery
- API endpoint returning trending papers
- 10+ unit tests

### Phase 2: Multi-Source Aggregation (Week 2)
**Goal**: Add Reddit and aggregation logic

- [ ] Implement `RedditSource`
- [ ] Implement `TrendAggregator`
- [ ] Add deduplication logic
- [ ] Implement trend scoring algorithm
- [ ] Add integration tests
- [ ] Create `/api/v1/trends/discover` endpoint

**Deliverables**:
- Multi-source trend discovery
- Combined trend scoring
- Performance benchmarks

### Phase 3: Agent Integration (Week 3)
**Goal**: Integrate with existing researcher agent

- [ ] Add `discover_trending_node` to LangGraph
- [ ] Update researcher agent to use trending data
- [ ] Add hybrid ranking (relevance + trend)
- [ ] Update frontend to display trend badges
- [ ] Add discussion links to UI

**Deliverables**:
- Enhanced discovery endpoint
- Frontend showing "trending" badge
- Links to HN/Reddit discussions

### Phase 4: Additional Sources (Week 4+)
**Goal**: Expand source coverage

- [ ] Implement `PapersWithCodeSource`
- [ ] Implement `HuggingFaceSource`
- [ ] Implement `SemanticScholarSource`
- [ ] Add configurable source weights
- [ ] Add admin dashboard for monitoring

**Deliverables**:
- 5+ trend sources
- Configurable aggregation
- Monitoring dashboard

---

## Database Schema

Add a new table to track trending papers:

```sql
CREATE TABLE trending_papers (
    id SERIAL PRIMARY KEY,
    paper_id VARCHAR(50) NOT NULL,          -- arXiv ID
    trend_score FLOAT NOT NULL,
    total_mentions INT DEFAULT 0,
    total_engagement INT DEFAULT 0,
    trending_since TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL,
    sources JSONB,                           -- ["hackernews", "reddit"]
    signals JSONB,                           -- Array of TrendSignal objects
    discussion_urls JSONB,                   -- Links to discussions
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_paper_id (paper_id),
    INDEX idx_trend_score (trend_score DESC),
    INDEX idx_trending_since (trending_since DESC)
);
```

---

## API Endpoints

### 1. Get Trending Papers
```
GET /api/v1/trends/discover

Query Params:
- topic: str (optional, default="AI")
- time_window: int (hours, default=168)
- max_results: int (default=20)
- sources: str[] (optional, filter by sources)

Response:
{
  "papers": [
    {
      "id": "2401.12345",
      "title": "...",
      "trend_score": 87.5,
      "total_mentions": 15,
      "buzz_velocity": 2.3,
      "sources": ["hackernews", "reddit"],
      "discussion_urls": [
        "https://news.ycombinator.com/item?id=123456",
        "https://reddit.com/r/MachineLearning/..."
      ],
      "top_discussion_snippet": "This paper is groundbreaking..."
    }
  ],
  "metadata": {
    "sources_queried": ["hackernews", "reddit"],
    "total_signals": 47,
    "time_window_hours": 168
  }
}
```

### 2. Get Source-Specific Trends
```
GET /api/v1/trends/hackernews
GET /api/v1/trends/reddit
```

---

## Caching Strategy

- **Source cache**: 1 hour TTL (avoid hammering APIs)
- **Trend scores**: 6 hour TTL (recompute periodically)
- **Paper metadata**: 24 hour TTL (static data)

```python
from functools import lru_cache
import time

class CachedTrendSource:
    def __init__(self, source: TrendSource, ttl: int = 3600):
        self.source = source
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}

    async def fetch_trending(self, topic: str) -> List[TrendSignal]:
        cache_key = f"{topic}"
        now = time.time()

        if cache_key in self._cache:
            if now - self._timestamps[cache_key] < self.ttl:
                return self._cache[cache_key]

        # Fetch fresh data
        signals = await self.source.fetch_trending(topic)
        self._cache[cache_key] = signals
        self._timestamps[cache_key] = now

        return signals
```

---

## Testing Strategy

### Unit Tests
- [x] TrendSource implementations (mock API responses)
- [x] Paper ID extraction from various URL formats
- [x] Engagement score calculations
- [x] Trend score algorithm
- [x] Cache behavior

### Integration Tests
- [x] HackerNews API integration (real API calls)
- [x] Reddit API integration
- [x] Multi-source aggregation
- [x] Database persistence

### E2E Tests
- [x] Full trend discovery flow
- [x] API endpoint responses
- [x] Frontend integration

---

## Frontend Enhancements

### Trending Badge
```tsx
{paper.trend_score > 70 && (
  <span className={styles.trendingBadge}>
    🔥 Trending
  </span>
)}
```

### Discussion Links
```tsx
<div className={styles.discussions}>
  <h4>Discussions:</h4>
  {paper.discussion_urls.map(url => (
    <a href={url} target="_blank" rel="noopener noreferrer">
      {getSourceName(url)} ({getEngagement(url)})
    </a>
  ))}
</div>
```

### Trend Score Visualization
```tsx
<TrendMeter score={paper.trend_score} />
```

---

## Monitoring & Analytics

Track:
- API response times per source
- Cache hit rates
- Papers discovered per source
- User engagement with trending papers
- Source reliability (uptime, data quality)

---

## Future Enhancements

1. **Real-time Trend Alerts**: Notify when a paper's buzz velocity spikes
2. **Personalized Trends**: Learn user preferences, weight sources accordingly
3. **Trend Explanations**: "Trending because: 47 upvotes on HN, 3 Reddit discussions"
4. **Historical Trends**: "This paper was trending 2 weeks ago"
5. **Comparative Trends**: "More buzz than 95% of papers this week"
6. **Author Tracking**: Track trending authors, not just papers
7. **Topic Clustering**: Auto-detect emerging sub-topics (e.g., "constitutional AI")

---

## Cost Analysis (Free Tier)

| Source | Free Tier | Rate Limit | Cost at Scale |
|--------|-----------|------------|---------------|
| HackerNews | Unlimited | None | **$0** |
| Reddit | 100 req/min | 100/min | **$0** |
| Papers w/Code | Unlimited | Reasonable | **$0** |
| Semantic Scholar | 100 req/sec | 100/s | **$0** |
| **Total** | - | - | **$0/month** ✅ |

**Scalability**: If you exceed free tiers, costs are minimal ($5-20/month) for moderate usage.

---

## Success Metrics

- **Discovery Rate**: % of trending papers captured vs manual search
- **Relevance**: % of trending papers user finds interesting
- **Engagement**: Click-through rate on discussion links
- **Coverage**: Number of sources providing signals
- **Freshness**: Average age of trending papers discovered

---

## Next Steps

1. ✅ Review and approve this design
2. Create `app/services/trends/` structure
3. Implement HackerNews source (Phase 1)
4. Test with sample queries
5. Iterate based on results

Ready to proceed with implementation?
