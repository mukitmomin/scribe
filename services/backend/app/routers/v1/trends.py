"""
Trend Discovery API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.services.trends.aggregator import TrendAggregator
from app.services.trends.sources.hackernews import HackerNewsSource
from app.services.arxiv_service import ArxivService


router = APIRouter(prefix="/api/v1/trends", tags=["trends"])


# Response models
class TrendingPaperResponse(BaseModel):
    """Response model for a single trending paper."""

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
    trending_reasons: List[str]
    top_discussion_snippet: str


class TrendDiscoveryMetadata(BaseModel):
    """Metadata about the trend discovery process."""

    sources_queried: List[str]
    total_papers_found: int
    time_window_hours: int
    topic: str
    cache_hit: bool = False


class TrendDiscoveryResponse(BaseModel):
    """Complete response for trend discovery."""

    papers: List[TrendingPaperResponse]
    metadata: TrendDiscoveryMetadata


@router.get("/discover", response_model=TrendDiscoveryResponse)
async def discover_trending_papers(
    topic: str = Query("AI", description="Topic to search for (e.g., 'AI', 'LLM', 'ML')"),
    time_window: int = Query(
        168, description="Time window in hours (default: 1 week)", ge=1, le=720
    ),
    max_results: int = Query(20, description="Maximum results to return", ge=1, le=100),
):
    """
    Discover trending papers based on social media buzz.

    This endpoint aggregates signals from multiple sources (currently HackerNews)
    to identify papers that are gaining attention in the AI community.

    **Current sources**:
    - HackerNews (free, no auth required)

    **Future sources**:
    - Reddit (r/MachineLearning, r/LocalLLaMA)
    - Papers with Code
    - Hugging Face
    - Twitter/X (when budget allows)

    **Query Parameters**:
    - `topic`: Filter by topic (e.g., "LLM", "GenAI", "Agents")
    - `time_window`: How many hours back to search (1-720)
    - `max_results`: Maximum papers to return (1-100)

    **Returns**:
    - List of trending papers with trend scores, engagement metrics, and discussion links
    - Metadata about the search process
    """
    try:
        # Initialize aggregator with HackerNews source
        # Future: Add more sources based on config/user preferences
        aggregator = TrendAggregator(
            sources=[HackerNewsSource()], arxiv_service=ArxivService()
        )

        # Discover trending papers
        trending_papers = await aggregator.discover_trending_papers(
            topic=topic, time_window_hours=time_window, max_results=max_results
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
                trending_reasons=p.trending_reasons,
                top_discussion_snippet=p.top_discussion_snippet,
            )
            for p in trending_papers
        ]

        return TrendDiscoveryResponse(
            papers=papers_response,
            metadata=TrendDiscoveryMetadata(
                sources_queried=["hackernews"],
                total_papers_found=len(papers_response),
                time_window_hours=time_window,
                topic=topic,
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error discovering trends: {str(e)}"
        )


@router.get("/hackernews", response_model=List[TrendingPaperResponse])
async def get_hackernews_trends(
    time_window: int = Query(168, description="Time window in hours", ge=1, le=720),
    max_results: int = Query(20, description="Maximum results", ge=1, le=100),
):
    """
    Get trending papers specifically from HackerNews.

    Simplified endpoint that returns raw signals from HackerNews without
    full arXiv enrichment. Useful for debugging and testing.

    **Query Parameters**:
    - `time_window`: How many hours back to search
    - `max_results`: Maximum signals to return

    **Returns**:
    - List of papers mentioned on HackerNews with engagement metrics
    """
    try:
        source = HackerNewsSource()
        signals = await source.fetch_trending(
            topic="AI", time_window_hours=time_window, max_results=max_results
        )

        # Convert signals to simplified response
        # (without full arXiv enrichment)
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
                buzz_velocity=0.0,
                sources=["hackernews"],
                discussion_urls=[s.discussion_url],
                trending_reasons=[f"{s.upvotes} points, {s.comments} comments"],
                top_discussion_snippet=s.discussion_snippet,
            )
            for s in signals
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching HackerNews trends: {str(e)}"
        )
