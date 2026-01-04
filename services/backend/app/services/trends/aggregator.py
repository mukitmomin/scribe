"""
Trend aggregator for combining signals from multiple sources.
"""

import asyncio
import math
from typing import List, Dict
from datetime import datetime
from collections import defaultdict

from .base import TrendSource
from .models import TrendSignal, TrendingPaper
from app.services.arxiv_service import ArxivService


class TrendAggregator:
    """
    Aggregate trend signals from multiple sources.

    Fetches signals from all sources, deduplicates by paper ID,
    enriches with arXiv metadata, computes trend scores, and ranks results.
    """

    def __init__(
        self,
        sources: List[TrendSource],
        arxiv_service: ArxivService = None,
    ):
        """
        Initialize the aggregator.

        Args:
            sources: List of TrendSource implementations
            arxiv_service: ArxivService instance (creates new if None)
        """
        self.sources = sources
        self.arxiv_service = arxiv_service or ArxivService()

    async def discover_trending_papers(
        self,
        topic: str = "AI",
        time_window_hours: int = 168,
        max_results: int = 20,
        scoring_weights: Dict[str, float] = None,
        source_weights: Dict[str, float] = None,
    ) -> List[TrendingPaper]:
        """
        Discover trending papers by aggregating signals from all sources.

        Steps:
        1. Fetch signals from all sources (parallel)
        2. Group signals by paper ID
        3. Fetch paper metadata from arXiv
        4. Compute trend scores
        5. Rank and return top papers

        Args:
            topic: Topic to search for
            time_window_hours: How far back to look
            max_results: Maximum papers to return
            scoring_weights: Custom weights for trend scoring
            source_weights: Custom weights for sources

        Returns:
            List of TrendingPaper objects, ranked by trend score
        """
        # Step 1: Fetch from all sources concurrently
        signals = await self._fetch_all_sources(topic, time_window_hours)

        if not signals:
            return []

        # Apply source weights if provided
        if source_weights:
            signals = self._apply_source_weights(signals, source_weights)

        # Step 2: Group by paper ID
        papers_map = self._group_by_paper(signals)

        # Step 3: Fetch arXiv metadata for each paper
        trending_papers = await self._enrich_with_arxiv_data(papers_map)

        # Step 4: Compute trend scores
        weights = scoring_weights or {
            "engagement": 0.4,
            "recency": 0.3,
            "authority": 0.2,
            "velocity": 0.1,
        }

        for paper in trending_papers:
            paper.trend_score = self._compute_trend_score(paper, weights)
            paper.trending_reasons = self._generate_trending_reasons(paper)

        # Step 5: Rank by trend score
        trending_papers.sort(key=lambda p: p.trend_score, reverse=True)

        return trending_papers[:max_results]

    async def _fetch_all_sources(
        self, topic: str, time_window_hours: int
    ) -> List[TrendSignal]:
        """Fetch signals from all sources in parallel."""
        tasks = [
            source.fetch_trending(topic, time_window_hours) for source in self.sources
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and filter out errors
        all_signals = []
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_signals.extend(result)
            else:
                source_name = self.sources[i].__class__.__name__
                print(f"Error fetching from {source_name}: {result}")

        return all_signals

    def _apply_source_weights(
        self, signals: List[TrendSignal], source_weights: Dict[str, float]
    ) -> List[TrendSignal]:
        """Apply source weights to engagement scores."""
        for signal in signals:
            weight = source_weights.get(signal.source, 1.0)
            signal.engagement_score *= weight

        return signals

    def _group_by_paper(
        self, signals: List[TrendSignal]
    ) -> Dict[str, List[TrendSignal]]:
        """Group signals by paper ID."""
        papers_map = defaultdict(list)
        for signal in signals:
            papers_map[signal.paper_id].append(signal)
        return papers_map

    async def _enrich_with_arxiv_data(
        self, papers_map: Dict[str, List[TrendSignal]]
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
            if signals:
                top_signal = max(signals, key=lambda s: s.engagement_score)
                trending_paper.top_discussion_snippet = top_signal.discussion_snippet

            # Compute buzz velocity (mentions per day)
            if trending_paper.trending_since:
                age_days = (datetime.now() - trending_paper.trending_since).days or 1
                trending_paper.buzz_velocity = len(signals) / age_days

            trending_papers.append(trending_paper)

        return trending_papers

    def _compute_trend_score(
        self, paper: TrendingPaper, weights: Dict[str, float]
    ) -> float:
        """
        Compute multi-factor trend score.

        Score = Σ(weight_i × component_i)

        Components:
        - Engagement: Total interactions (upvotes, comments, shares)
        - Recency: Exponential decay based on age
        - Authority: Average credibility of discussants
        - Velocity: Mentions per day

        Returns:
            Score from 0-100
        """
        # 1. Engagement component (0-100)
        total_engagement = sum(
            s.upvotes + (s.comments * 2) + (s.shares * 3) for s in paper.signals
        )
        engagement_score = min(100, total_engagement / 10)

        # 2. Recency component (0-100)
        # Use exponential decay: older = lower score
        if paper.trending_since:
            age_days = (datetime.now() - paper.trending_since).days
            recency_score = 100 * math.exp(-age_days / 7)  # 7-day half-life
        else:
            recency_score = 50  # Default if no timestamp

        # 3. Authority component (0-100)
        # Average credibility of authors/discussants
        if paper.signals:
            authority_score = (
                100 * sum(s.author_credibility for s in paper.signals) / len(paper.signals)
            )
        else:
            authority_score = 50

        # 4. Buzz velocity component (0-100)
        # Papers gaining traction quickly get higher scores
        velocity_score = min(100, paper.buzz_velocity * 20)

        # Weighted combination
        trend_score = (
            weights.get("engagement", 0.4) * engagement_score
            + weights.get("recency", 0.3) * recency_score
            + weights.get("authority", 0.2) * authority_score
            + weights.get("velocity", 0.1) * velocity_score
        )

        return round(trend_score, 2)

    def _generate_trending_reasons(self, paper: TrendingPaper) -> List[str]:
        """Generate human-readable explanations for why a paper is trending."""
        reasons = []

        # Mention count
        if paper.total_mentions > 5:
            reasons.append(f"Discussed in {paper.total_mentions} places")
        elif paper.total_mentions > 1:
            reasons.append(f"Discussed in {paper.total_mentions} places")

        # Total engagement
        if paper.total_engagement > 200:
            reasons.append(f"{paper.total_engagement} total interactions")

        # Velocity
        if paper.buzz_velocity > 2:
            reasons.append(f"Rapidly trending ({paper.buzz_velocity:.1f} mentions/day)")

        # Source-specific reasons (top 2)
        source_reasons = []
        for signal in sorted(paper.signals, key=lambda s: s.engagement_score, reverse=True)[
            :2
        ]:
            if signal.source == "hackernews" and signal.upvotes > 50:
                source_reasons.append(f"{signal.upvotes} points on HackerNews")
            elif signal.source == "reddit" and signal.upvotes > 50:
                source_reasons.append(f"{signal.upvotes} upvotes on Reddit")
            elif signal.comments > 20:
                source_reasons.append(f"{signal.comments} comments on {signal.source}")

        reasons.extend(source_reasons)

        # If no specific reasons, provide a generic one
        if not reasons:
            reasons.append("Gaining community attention")

        return reasons[:4]  # Return top 4 reasons
