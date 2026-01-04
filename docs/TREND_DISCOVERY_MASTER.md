# Trend Discovery Feature - Master Reference Design

> **Single Source of Truth**: This document contains the complete design for the social trend discovery feature including architecture, UI, agent intelligence, and implementation plan.

**Last Updated**: 2026-01-04
**Status**: Design Complete → Phase 1 Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Goals & Requirements](#goals--requirements)
3. [Architecture](#architecture)
4. [Source Strategy](#source-strategy)
5. [Agent Intelligence](#agent-intelligence)
6. [UI Design](#ui-design)
7. [API Design](#api-design)
8. [Database Schema](#database-schema)
9. [Implementation Phases](#implementation-phases)
10. [Testing Strategy](#testing-strategy)
11. [Future Enhancements](#future-enhancements)

---

## Overview

### What is Trend Discovery?

An intelligent system that discovers trending AI/ML research papers by analyzing social media buzz, expert discussions, and community engagement across platforms like HackerNews, Reddit, GitHub, and Twitter.

### Why?

**User Goal**: Stay on top of industry trends to:
- Learn about cutting-edge research before it goes mainstream
- Understand what AI experts and practitioners are discussing
- Find interesting papers to write about and create demos for
- Build a portfolio of trend-aware content

### How?

**Agentic Approach**: User provides minimal intent (e.g., "show me hot LLM papers"), agent interprets this intelligently and searches multiple sources, scores papers by engagement + recency + authority, and returns ranked results with explanations.

---

## Goals & Requirements

### Functional Requirements

1. ✅ Discover papers with significant social buzz
2. ✅ Aggregate signals from multiple platforms
3. ✅ Rank by combined trend score (engagement + recency + authority)
4. ✅ Extensible architecture for adding new sources
5. ✅ Minimal UI configuration (1 required input, 4 optional)
6. ✅ Agent-driven intelligence (interprets user intent)
7. ✅ Explainable results (show WHY papers are trending)

### Non-Functional Requirements

1. ✅ Free/low-cost implementation (start with free APIs)
2. ✅ Fast response times (<5s)
3. ✅ Respect API rate limits with caching
4. ✅ Graceful degradation if source unavailable
5. ✅ Testable, maintainable code

---

## Architecture

### High-Level System Design

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Discovery Page                                         │  │
│  │  - DiscoveryFocusSelector (Hot/Emerging/Hidden/Deep)   │  │
│  │  - TopicSelector (LLMs, GenAI, Agents, etc.)           │  │
│  │  - CommunitySelector (Researchers/Practitioners/etc.)  │  │
│  │  - Results Display with Trending Reasons               │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────┘
                            │ POST /api/v1/trends/discover
                            │ { discovery_focus, topic_areas, ... }
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           TrendDiscoveryAgent (Intelligence)           │  │
│  │  - Interprets user intent                              │  │
│  │  - Generates search keywords from topics               │  │
│  │  - Configures source weights                           │  │
│  │  - Sets scoring parameters                             │  │
│  └────────────────┬───────────────────────────────────────┘  │
│                   │                                           │
│  ┌────────────────▼───────────────────────────────────────┐  │
│  │              TrendAggregator                           │  │
│  │  - Fetches from all sources in parallel               │  │
│  │  - Deduplicates by paper ID                            │  │
│  │  - Enriches with arXiv metadata                        │  │
│  │  - Computes trend scores                               │  │
│  │  - Ranks and returns top N                             │  │
│  └────────────────┬───────────────────────────────────────┘  │
│                   │                                           │
│         ┌─────────┴──────────┬──────────────┐                │
│         ▼                    ▼              ▼                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ HackerNews   │  │   Reddit     │  │ Papers with  │       │
│  │   Source     │  │   Source     │  │    Code      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                   │               │                │
└─────────┼───────────────────┼───────────────┼────────────────┘
          │                   │               │
          ▼                   ▼               ▼
     HN API              Reddit API      PWC API
```

### Core Components

#### 1. TrendSource (Abstract Base)

**File**: `app/services/trends/base.py`

```python
class TrendSource(ABC):
    """Abstract base class for all trend sources."""

    @abstractmethod
    async def fetch_trending(
        self, topic: str, time_window_hours: int, max_results: int
    ) -> List[TrendSignal]

    @abstractmethod
    def extract_paper_id(self, text: str) -> Optional[str]

    def compute_engagement_score(self, signal: TrendSignal) -> float
```

**Responsibilities**:
- Define interface for all sources
- Provide caching utilities
- Common paper ID extraction patterns

#### 2. TrendSignal & TrendingPaper (Data Models)

**File**: `app/services/trends/models.py`

```python
@dataclass
class TrendSignal:
    """A single mention of a paper on a platform."""
    source: str              # "hackernews", "reddit", etc.
    paper_id: str            # arXiv ID
    paper_title: str
    discussion_url: str
    timestamp: datetime
    upvotes: int
    comments: int
    engagement_score: float
    discussion_snippet: str
    metadata: dict

@dataclass
class TrendingPaper:
    """Paper with aggregated trend data."""
    paper_id: str
    title: str
    authors: List[str]
    summary: str
    published_date: str
    pdf_url: str
    trend_score: float
    total_mentions: int
    total_engagement: int
    buzz_velocity: float    # mentions/day
    sources: List[str]
    signals: List[TrendSignal]
    discussion_urls: List[str]
    trending_reasons: List[str]  # Human-readable
```

#### 3. HackerNewsSource (Implementation)

**File**: `app/services/trends/sources/hackernews.py`

```python
class HackerNewsSource(TrendSource):
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    async def fetch_trending(...) -> List[TrendSignal]:
        # 1. Fetch top stories
        # 2. Filter for arXiv links
        # 3. Extract engagement metrics
        # 4. Return as TrendSignals
```

**Data Flow**:
```
HN API → Top Stories → Filter arXiv → Extract Metrics → TrendSignals
```

#### 4. TrendAggregator (Orchestrator)

**File**: `app/services/trends/aggregator.py`

```python
class TrendAggregator:
    async def discover_trending_papers(...) -> List[TrendingPaper]:
        # 1. Fetch from all sources (parallel)
        # 2. Group by paper ID
        # 3. Fetch arXiv metadata
        # 4. Compute trend scores
        # 5. Rank and return
```

#### 5. TrendDiscoveryAgent (Intelligence)

**File**: `app/agents/trend_discovery.py`

```python
class TrendDiscoveryAgent:
    async def execute(state: TrendDiscoveryState) -> TrendDiscoveryState:
        # 1. Interpret discovery focus
        # 2. Generate topic keywords
        # 3. Configure sources
        # 4. Execute discovery
        # 5. Add explanations
```

---

## Source Strategy

### Phase 1: HackerNews (PRIMARY)

| Aspect | Details |
|--------|---------|
| **API** | https://hacker-news.firebaseio.com/v0 |
| **Cost** | ✅ FREE, no authentication |
| **Ease** | ⭐⭐⭐⭐⭐ Simple REST API |
| **Quality** | ⭐⭐⭐⭐⭐ High signal-to-noise |
| **Volume** | ⭐⭐⭐ 10-20 AI papers/week |
| **Implementation** | ~4-6 hours |

**Endpoints Used**:
```
GET /topstories.json     → [story_id1, story_id2, ...]
GET /item/{id}.json      → { title, url, score, descendants, ... }
```

**Paper Detection**:
- Stories with `arxiv.org/abs/` or `arxiv.org/pdf/` in URL
- Titles containing `[YYMM.NNNNN]` patterns
- Calculate engagement: `points + (comments × 2)`

### Phase 2: Reddit (SECONDARY)

| Aspect | Details |
|--------|---------|
| **Subreddits** | r/MachineLearning, r/LocalLLaMA, r/LanguageTechnology |
| **Cost** | ✅ FREE (100 req/min) |
| **Ease** | ⭐⭐⭐ Requires OAuth |
| **Quality** | ⭐⭐⭐⭐ Good discussions |
| **Volume** | ⭐⭐⭐⭐ 20-50 papers/week |
| **Implementation** | ~6-8 hours |

### Phase 3+: Additional Sources

- **Papers with Code**: GitHub stars, implementation counts
- **Hugging Face**: Model downloads, trending models
- **Semantic Scholar**: Citation velocity, influence metrics
- **Twitter/X**: (Future - expensive API)

### Source Priority Matrix

```
               High Quality
                    ↑
                    │
    HackerNews ●────┤
                    │    Papers with Code ●
                    │
    Reddit ●────────┤────────────● Semantic Scholar
                    │
Low Volume ─────────┼──────────────────→ High Volume
                    │
                    │    ● Twitter (expensive)
                    │
                    ↓
               Low Quality
```

---

## Agent Intelligence

### Philosophy

**Agent = Intelligence, UI = Intent**

User provides high-level intent via simple controls. Agent translates this into detailed search strategy.

### Discovery Focus Modes

| Mode | Time Window | Scoring Weights | Min Engagement | Description |
|------|-------------|-----------------|----------------|-------------|
| **🔥 Hot Right Now** | 3 days | 60% Engagement<br>40% Recency | 50+ | High engagement, very recent |
| **📈 Emerging Trends** | 14 days | 30% Engagement<br>40% Velocity<br>30% Recency | 20+ | Rapidly gaining traction |
| **💎 Hidden Gems** | 30 days | 20% Engagement<br>40% Authority<br>40% Uniqueness | 5+ | Quality but under-discussed |
| **🎯 Deep Dives** | 90 days | 20% Engagement<br>50% Authority<br>30% Discussion Depth | 10+ | Expert analysis, thoughtful discussions |

### Topic Keyword Expansion

Agent expands simple topics into comprehensive search terms:

```python
TOPIC_KEYWORDS = {
    "llm": [
        "large language model", "LLM", "GPT", "transformer",
        "in-context learning", "prompt", "instruction tuning",
        "RLHF", "alignment", "fine-tuning"
    ],
    "genai": [
        "generative", "diffusion", "GAN", "VAE",
        "text-to-image", "stable diffusion", "DALL-E"
    ],
    "agents": [
        "agent", "autonomous", "reasoning", "planning",
        "tool use", "ReAct", "chain of thought", "multi-agent"
    ],
    "vision": [
        "computer vision", "image", "video", "segmentation",
        "detection", "ViT", "CLIP", "multimodal"
    ],
    "safety": [
        "interpretability", "explainability", "safety",
        "alignment", "robustness", "adversarial"
    ],
    "efficiency": [
        "efficient", "optimization", "quantization",
        "pruning", "distillation", "compression"
    ]
}
```

### Community-Based Source Weighting

```python
def configure_sources(communities: List[str]) -> Dict[str, float]:
    weights = {
        "hackernews": 1.0,
        "reddit": 1.0,
        "paperswithcode": 1.0,
        "huggingface": 1.0
    }

    if "researchers" not in communities:
        weights["hackernews"] *= 0.5
        weights["paperswithcode"] *= 0.5

    if "practitioners" not in communities:
        weights["reddit"] *= 0.3

    if "builders" not in communities:
        weights["huggingface"] *= 0.3

    return weights
```

### Trend Scoring Algorithm

```python
def compute_trend_score(paper: TrendingPaper, weights: dict) -> float:
    """
    Multi-factor scoring combining:
    - Engagement (upvotes + comments + shares)
    - Recency (exponential decay)
    - Authority (discussant credibility)
    - Velocity (mentions per day)
    """

    # Engagement (0-100)
    total_engagement = sum(
        s.upvotes + (s.comments * 2) + (s.shares * 3)
        for s in paper.signals
    )
    engagement_score = min(100, total_engagement / 10)

    # Recency (0-100) with 7-day half-life
    age_days = (datetime.now() - paper.trending_since).days
    recency_score = 100 * math.exp(-age_days / 7)

    # Authority (0-100)
    authority_score = 100 * sum(
        s.author_credibility for s in paper.signals
    ) / len(paper.signals)

    # Velocity bonus (0-20)
    velocity_bonus = min(20, paper.buzz_velocity * 5)

    # Weighted combination
    score = (
        weights.get("engagement", 0.4) * engagement_score +
        weights.get("recency", 0.3) * recency_score +
        weights.get("authority", 0.2) * authority_score +
        weights.get("velocity", 0.1) * velocity_bonus
    )

    return round(score, 2)
```

### Trend Explanations

Agent generates human-readable reasons:

```python
def generate_trending_reasons(paper: TrendingPaper) -> List[str]:
    reasons = []

    if paper.total_mentions > 5:
        reasons.append(f"Discussed in {paper.total_mentions} places")

    if paper.total_engagement > 200:
        reasons.append(f"{paper.total_engagement} total interactions")

    if paper.buzz_velocity > 2:
        reasons.append(f"Rapidly trending ({paper.buzz_velocity:.1f}/day)")

    # Source-specific
    for signal in sorted(paper.signals, key=lambda s: s.engagement_score, reverse=True)[:2]:
        if signal.source == "hackernews" and signal.upvotes > 100:
            reasons.append(f"{signal.upvotes} points on HackerNews")
        if signal.source == "reddit" and signal.upvotes > 50:
            reasons.append(f"{signal.upvotes} upvotes on Reddit")

    return reasons
```

---

## UI Design

### Design Principles

1. **Minimal Configuration**: 1 required input, 4 optional
2. **Progressive Disclosure**: Advanced options hidden by default
3. **Smart Defaults**: Works perfectly with zero configuration
4. **Explainability**: Users understand why results appear
5. **Agent-Driven**: UI provides intent, agent provides intelligence

### UI Controls

#### 1. Discovery Focus (Required)

**Component**: `DiscoveryFocusSelector`
**Type**: Segmented control / Radio group

```tsx
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ 🔥   │ │ 📈   │ │ 💎   │ │ 🎯   │
│ Hot  │ │Emerg.│ │Hidden│ │ Deep │
└──●───┘ └──────┘ └──────┘ └──────┘
     ↑ Selected
```

**Options**:
- 🔥 Hot Right Now
- 📈 Emerging Trends
- 💎 Hidden Gems
- 🎯 Deep Dives

#### 2. Topic Areas (Optional)

**Component**: `TopicSelector`
**Type**: Multi-select chips (max 3)

```tsx
[🤖 LLMs] [🎨 GenAI] [🧠 Agents] [👁️ Vision]
[🔬 Safety] [⚡ Efficiency]
```

#### 3. Community Perspectives (Optional)

**Component**: `CommunitySelector`
**Type**: Checkboxes (multi-select)

```tsx
☑ Researchers (HackerNews, Papers with Code)
☑ Practitioners (Reddit communities)
☑ Builders (GitHub, Hugging Face)
```

#### 4. Recency Slider (Advanced - Collapsible)

**Component**: `RecencySlider`
**Type**: Range slider

```tsx
[Past 24h] ──●────────── [Past 6 months]
             ↑ Default: 1 week
```

#### 5. Search Query (Optional - Smart)

**Component**: `SearchInput`
**Type**: Text input with smart detection

```tsx
┌─────────────────────────────────────────────┐
│ Optional: 'attention mechanisms' or arXiv ID│
└─────────────────────────────────────────────┘
```

### Page Layout

```
┌─────────────────────────────────────────────────────┐
│  📊 Discover Trending Papers                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  What type of trends are you looking for?           │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │ 🔥   │ │ 📈   │ │ 💎   │ │ 🎯   │              │
│  └──●───┘ └──────┘ └──────┘ └──────┘              │
│                                                      │
│  ▼ Advanced Options                                 │
│  ┌────────────────────────────────────────────┐    │
│  │ Topic Areas: [🤖 LLMs] [🧠 Agents]         │    │
│  │ Communities: ☑ All                          │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  [🔍 Discover Trending Papers]                      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  📈 15 Trending Papers Found                         │
├─────────────────────────────────────────────────────┤
│  1. Constitutional AI: Harmlessness from AI...      │
│     [2401.12345] • 87.5 trend score • 🔥 Trending   │
│     Trending because:                                │
│     • 247 points on HackerNews                       │
│     • Discussed in 3 places                          │
│     • Rapidly trending (2.3 mentions/day)            │
│     [💬 Discussions] [📄 Read] [🔖 Save]            │
│                                                      │
│  2. Efficient Streaming Language Models...          │
│     [2309.17453] • 82.3 trend score • 📈 Rising     │
│     ...                                              │
└─────────────────────────────────────────────────────┘
```

### Zero Configuration Flow

User just clicks "Discover" with defaults:

```
Discovery Focus: Hot Right Now ✓ (default)
Topic Areas: (none - all AI topics)
Communities: All ✓ (default)
   ↓
Agent generates comprehensive search
   ↓
Returns top 10 hot papers from past 3 days
```

---

## API Design

### Endpoint: POST /api/v1/trends/discover

**Request**:
```json
{
  "discovery_focus": "hot",
  "topic_areas": ["llm", "agents"],
  "communities": ["researchers", "practitioners"],
  "recency_days": 7,
  "search_query": null
}
```

**Response**:
```json
{
  "papers": [
    {
      "id": "2401.12345",
      "title": "Constitutional AI: Harmlessness from AI Feedback",
      "authors": ["Anthropic Team"],
      "summary": "We propose a method for training...",
      "published_date": "2024-01-15",
      "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
      "trend_score": 87.5,
      "total_mentions": 3,
      "total_engagement": 520,
      "buzz_velocity": 2.3,
      "sources": ["hackernews", "reddit"],
      "discussion_urls": [
        "https://news.ycombinator.com/item?id=123456",
        "https://reddit.com/r/MachineLearning/..."
      ],
      "trending_reasons": [
        "247 points on HackerNews",
        "Discussed in 3 places",
        "Rapidly trending (2.3 mentions/day)"
      ],
      "top_discussion_snippet": "This is groundbreaking work..."
    }
  ],
  "metadata": {
    "strategy_used": {
      "discovery_focus": "hot",
      "time_window_hours": 72,
      "generated_keywords": ["LLM", "GPT", "transformer", "agent", "reasoning"],
      "scoring_weights": {
        "engagement": 0.6,
        "recency": 0.4
      },
      "sources_queried": ["hackernews"],
      "min_engagement": 50
    },
    "total_papers_found": 15,
    "cache_hit": false
  }
}
```

### Endpoint: GET /api/v1/trends/hackernews

Simplified endpoint for HackerNews-only trends (for testing/debugging).

---

## Database Schema

### Table: trending_papers

```sql
CREATE TABLE trending_papers (
    id SERIAL PRIMARY KEY,
    paper_id VARCHAR(50) NOT NULL,
    trend_score FLOAT NOT NULL,
    total_mentions INT DEFAULT 0,
    total_engagement INT DEFAULT 0,
    trending_since TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL,
    sources JSONB,                  -- ["hackernews", "reddit"]
    signals JSONB,                  -- Array of TrendSignal objects
    discussion_urls JSONB,          -- Array of URLs
    trending_reasons JSONB,         -- Array of reason strings
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_paper_id (paper_id),
    INDEX idx_trend_score (trend_score DESC),
    INDEX idx_trending_since (trending_since DESC),
    INDEX idx_last_updated (last_updated DESC)
);
```

### Caching Strategy

- **Source cache**: 1 hour TTL (avoid API rate limits)
- **Trend scores**: 6 hour TTL (balance freshness vs. computation)
- **Paper metadata**: 24 hour TTL (arXiv data is static)

---

## Implementation Phases

### Phase 1: HackerNews Foundation (Week 1)

**Goal**: Single source, working end-to-end

**Tasks**:
- [x] Design complete ✓
- [ ] Create `app/services/trends/` directory structure
- [ ] Implement base classes (`TrendSource`, models)
- [ ] Implement `HackerNewsSource`
- [ ] Implement `TrendAggregator` (single source)
- [ ] Create `/api/v1/trends/discover` endpoint
- [ ] Add unit tests (10+ tests)
- [ ] Manual testing with real HN API

**Deliverables**:
- Working HackerNews trend discovery
- API returns top trending papers
- 10+ unit tests passing

**Effort**: ~8-12 hours

### Phase 2: Multi-Source Aggregation (Week 2)

**Goal**: Add Reddit, full aggregation logic

**Tasks**:
- [ ] Implement `RedditSource` with OAuth
- [ ] Update `TrendAggregator` for multi-source
- [ ] Implement deduplication logic
- [ ] Add trend scoring algorithm
- [ ] Add integration tests
- [ ] Database persistence (optional)

**Deliverables**:
- Two sources aggregated
- Combined trend scoring
- Performance benchmarks

**Effort**: ~12-16 hours

### Phase 3: Agent & UI Integration (Week 3)

**Goal**: Full agent intelligence, frontend

**Tasks**:
- [ ] Implement `TrendDiscoveryAgent`
- [ ] Add topic keyword expansion
- [ ] Build React UI components
- [ ] Integrate with frontend
- [ ] Add trending badges to paper cards
- [ ] Discussion links in UI

**Deliverables**:
- Complete agent intelligence
- Working UI with all controls
- Beautiful results display

**Effort**: ~12-16 hours

### Phase 4: Additional Sources (Week 4+)

**Goal**: Expand coverage

**Tasks**:
- [ ] Add Papers with Code source
- [ ] Add Hugging Face source
- [ ] Add Semantic Scholar source
- [ ] Configurable source weights
- [ ] Monitoring dashboard

**Deliverables**:
- 5+ sources active
- Robust aggregation
- Admin tools

**Effort**: ~6-8 hours per source

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/services/trends/test_hackernews.py`

```python
- test_extract_paper_id_from_abs_url()
- test_extract_paper_id_from_pdf_url()
- test_extract_paper_id_with_version()
- test_fetch_trending()
- test_compute_engagement_score()
- test_cache_behavior()
```

**File**: `tests/unit/services/trends/test_aggregator.py`

```python
- test_group_by_paper()
- test_deduplicate_signals()
- test_trend_score_calculation()
- test_parallel_source_fetching()
```

### Integration Tests

**File**: `tests/integration/trends/test_api.py`

```python
- test_discover_endpoint()
- test_hackernews_endpoint()
- test_with_topic_filter()
- test_with_time_window()
```

### Test Coverage Goal

- Unit tests: >80%
- Integration tests: All API endpoints
- E2E tests: Full discovery flow

---

## Success Metrics

### Technical Metrics

- **Response Time**: <5s for discovery request
- **Cache Hit Rate**: >70% (reduce API calls)
- **Coverage**: Discover 80%+ of trending papers
- **Accuracy**: 90%+ of returned papers are relevant

### User Metrics

- **Engagement**: Click-through rate on discussion links
- **Relevance**: % of papers user saves/reads
- **Discovery Rate**: Papers found vs. manual search
- **Satisfaction**: User finds at least 1 interesting paper per session

---

## Future Enhancements

### Phase 5+

1. **Real-time Alerts**: Notify when a paper's buzz spikes
2. **Personalized Trends**: Learn user preferences, weight accordingly
3. **Historical Trends**: "This paper was trending 2 weeks ago"
4. **Author Tracking**: Track trending authors, not just papers
5. **Topic Clustering**: Auto-detect emerging sub-topics
6. **Comparative Analysis**: "More buzz than 95% of papers this week"
7. **Weekly Digests**: Email summary of top trends
8. **Twitter Integration**: Add when budget allows ($100+/mo)

---

## Cost Analysis

### Current (Free Tier)

| Source | Free Tier | Rate Limit | Monthly Cost |
|--------|-----------|------------|--------------|
| HackerNews | Unlimited | None | $0 |
| Reddit | 100 req/min | 100/min | $0 |
| Papers w/Code | Unlimited | Reasonable | $0 |
| Semantic Scholar | 100 req/s | 100/s | $0 |
| **Total** | - | - | **$0** ✅ |

### Future (If Scaled)

- Moderate usage: $0-5/month (within free tiers)
- Heavy usage: $5-20/month (if exceed free tiers)
- Twitter addition: +$100/month (if needed)

---

## File Structure

```
services/backend/app/
├── services/
│   └── trends/
│       ├── __init__.py
│       ├── base.py                 # TrendSource abstract class
│       ├── models.py               # TrendSignal, TrendingPaper
│       ├── aggregator.py           # TrendAggregator
│       ├── utils.py                # Paper ID extraction, caching
│       └── sources/
│           ├── __init__.py
│           ├── hackernews.py       # HackerNewsSource
│           ├── reddit.py           # RedditSource (Phase 2)
│           └── paperswithcode.py   # PapersWithCodeSource (Phase 3)
├── agents/
│   └── trend_discovery.py          # TrendDiscoveryAgent (Phase 3)
└── routers/
    └── v1/
        └── trends.py                # API endpoints

tests/
├── unit/
│   └── services/
│       └── trends/
│           ├── test_base.py
│           ├── test_hackernews.py
│           └── test_aggregator.py
└── integration/
    └── trends/
        └── test_api.py

apps/web/src/
├── app/
│   └── discover-trends/
│       └── page.tsx                # Main discovery page
└── components/
    └── TrendDiscovery/
        ├── DiscoveryFocusSelector.tsx
        ├── TopicSelector.tsx
        ├── CommunitySelector.tsx
        └── TrendingPaperCard.tsx
```

---

## Quick Reference

### For New Session Context

**What**: Social trend discovery for AI papers
**Why**: Stay on top of industry buzz to learn, write, and build demos
**How**: Agent interprets minimal UI inputs → searches HN/Reddit/etc → returns ranked papers with explanations

**Status**: Design complete → Phase 1 implementation starting

**Key Files**:
- This document: `docs/TREND_DISCOVERY_MASTER.md` (single source of truth)
- Implementation: `services/backend/app/services/trends/`
- Tests: `tests/unit/services/trends/`

**First Implementation**:
1. Create directory structure
2. Implement HackerNews source (FREE, easy)
3. Basic API endpoint
4. Unit tests
5. Manual testing

**Agent Philosophy**: User says "show me hot LLM papers" → Agent figures out time windows, keywords, source weights, scoring → Returns top 10 with "247 points on HN" explanations

---

## Appendix: Example Flows

### Example 1: Zero Configuration

```
User clicks: "Discover"
   ↓
Default: Hot Right Now, All topics, All sources
   ↓
Agent: 3-day window, high engagement weights
   ↓
HackerNews: 15 papers found
   ↓
Top 10 returned with trend scores
   ↓
UI: "Constitutional AI - 87.5 score - 247 HN points"
```

### Example 2: LLM Focus

```
User selects: Hot + [LLMs] topic
   ↓
Agent expands: ["LLM", "GPT", "transformer", "in-context learning", ...]
   ↓
HackerNews + Reddit (r/LocalLLaMA): 23 papers
   ↓
Filter by keywords, rank by engagement
   ↓
Top 10 LLM papers returned
```

### Example 3: Hidden Gems

```
User selects: Hidden Gems + [Safety]
   ↓
Agent: 30-day window, authority-weighted, low min engagement
   ↓
Search: "interpretability", "alignment", "safety", ...
   ↓
Find papers with 5-30 upvotes but high-quality discussions
   ↓
Return 30 under-discussed gems
```

---

**End of Master Reference Document**

This document should be provided at the start of any new agent session to understand the complete feature design.
