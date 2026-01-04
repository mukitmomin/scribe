"""
Data models for trend discovery service.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class TrendSignal:
    """
    A single mention/discussion of a paper on a platform.

    Represents one data point from a trend source (e.g., a HackerNews story,
    Reddit post, or GitHub repo mentioning an arXiv paper).
    """

    source: str  # "hackernews", "reddit", etc.
    paper_id: str  # arXiv ID (e.g., "2401.12345")
    paper_title: str
    discussion_url: str  # Link to the discussion
    timestamp: datetime

    # Engagement metrics (platform-specific)
    upvotes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0

    # Computed engagement score (0-100)
    engagement_score: float = 0.0

    # Context from the discussion
    discussion_snippet: str = ""  # Top comment or snippet
    author: str = ""
    author_credibility: float = 0.5  # 0-1 score (default: neutral)

    # Source-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate data after initialization."""
        if not self.paper_id:
            raise ValueError("paper_id is required")
        if not self.source:
            raise ValueError("source is required")


@dataclass
class TrendingPaper:
    """
    A paper with aggregated trend data from multiple sources.

    Combines multiple TrendSignals for the same paper into a unified view
    with computed trend metrics.
    """

    paper_id: str
    title: str
    authors: List[str]
    summary: str
    published_date: str
    pdf_url: str

    # Aggregated trend metrics
    trend_score: float = 0.0  # Combined score (0-100)
    total_mentions: int = 0  # Count across all sources
    total_engagement: int = 0  # Sum of all interactions
    trending_since: Optional[datetime] = None  # First mention timestamp
    buzz_velocity: float = 0.0  # Mentions per day

    # Source breakdown
    sources: List[str] = field(default_factory=list)  # ["hackernews", "reddit"]
    signals: List[TrendSignal] = field(default_factory=list)  # Individual mentions

    # Discussion context
    top_discussion_snippet: str = ""  # Most upvoted comment/discussion
    discussion_urls: List[str] = field(default_factory=list)  # Links to discussions

    # Human-readable explanations
    trending_reasons: List[str] = field(default_factory=list)  # Why is this trending?

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and compute derived fields."""
        if not self.paper_id:
            raise ValueError("paper_id is required")

        # Compute total mentions if not set
        if self.total_mentions == 0 and self.signals:
            self.total_mentions = len(self.signals)

        # Compute total engagement if not set
        if self.total_engagement == 0 and self.signals:
            self.total_engagement = sum(
                s.upvotes + s.comments + s.shares for s in self.signals
            )

        # Set trending_since to earliest signal if not set
        if self.trending_since is None and self.signals:
            self.trending_since = min(s.timestamp for s in self.signals)

        # Extract unique sources if not set
        if not self.sources and self.signals:
            self.sources = list(set(s.source for s in self.signals))

        # Collect discussion URLs if not set
        if not self.discussion_urls and self.signals:
            self.discussion_urls = [s.discussion_url for s in self.signals]


@dataclass
class TrendDiscoveryState:
    """
    State for the trend discovery agent.

    Captures user intent and agent-generated strategy.
    """

    # User inputs (from UI)
    discovery_focus: str = "hot"  # "hot", "emerging", "hidden", "deep"
    topic_areas: List[str] = field(default_factory=list)  # ["llm", "genai", "agents"]
    communities: List[str] = field(
        default_factory=lambda: ["researchers", "practitioners", "builders"]
    )
    recency_days: int = 7
    search_query: Optional[str] = None

    # Agent-generated strategy
    search_strategy: Dict[str, Any] = field(default_factory=dict)
    source_weights: Dict[str, float] = field(default_factory=dict)
    scoring_weights: Dict[str, float] = field(default_factory=dict)
    generated_keywords: List[str] = field(default_factory=list)

    # Results
    trending_papers: List[TrendingPaper] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
