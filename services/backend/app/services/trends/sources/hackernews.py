"""
HackerNews trend source implementation.

Fetches trending arXiv papers from HackerNews using their free public API.
"""

import httpx
import re
from typing import List, Optional
from datetime import datetime, timedelta

from ..base import TrendSource
from ..models import TrendSignal


class HackerNewsSource(TrendSource):
    """
    Fetch trending papers from HackerNews.

    Uses the HackerNews Firebase API to find stories with arXiv links
    and compute engagement metrics based on points and comments.
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    # arXiv pattern variations
    ARXIV_PATTERNS = [
        r"arxiv\.org/abs/(\d{4}\.\d{4,5})",
        r"arxiv\.org/pdf/(\d{4}\.\d{4,5})",
        r"arxiv:(\d{4}\.\d{4,5})",
        r"\[(\d{4}\.\d{4,5})\]",
    ]

    async def fetch_trending(
        self,
        topic: str = "AI",
        time_window_hours: int = 168,
        max_results: int = 50,
    ) -> List[TrendSignal]:
        """
        Fetch trending arXiv papers from HackerNews.

        Strategy:
        1. Get top stories from HN
        2. Filter for arXiv links
        3. Extract paper IDs and engagement metrics
        4. Return as TrendSignal objects

        Args:
            topic: Topic to search for (used for filtering)
            time_window_hours: How far back to look (default: 1 week)
            max_results: Maximum signals to return

        Returns:
            List of TrendSignal objects
        """
        # Check cache first
        cache_key = f"hn_{topic}_{time_window_hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        signals = []
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Fetch top story IDs
                response = await client.get(f"{self.BASE_URL}/topstories.json")
                response.raise_for_status()
                story_ids = response.json()[:200]  # Check top 200 stories

                # Fetch story details and filter for arXiv papers
                for story_id in story_ids[: max_results * 2]:  # Overfetch to account for filtering
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
                        },
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

            except Exception as e:
                print(f"Error fetching from HackerNews: {e}")
                # Return partial results if available
                pass

        # Save to cache
        self._save_to_cache(cache_key, signals)

        return signals

    async def _get_story(self, client: httpx.AsyncClient, story_id: int) -> Optional[dict]:
        """Fetch story details from HN API."""
        try:
            response = await client.get(f"{self.BASE_URL}/item/{story_id}.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching story {story_id}: {e}")
            return None

    async def _get_top_comment(
        self, client: httpx.AsyncClient, comment_ids: List[int]
    ) -> Optional[str]:
        """Fetch the first comment for context."""
        if not comment_ids:
            return None

        try:
            first_comment_id = comment_ids[0]
            response = await client.get(f"{self.BASE_URL}/item/{first_comment_id}.json")
            response.raise_for_status()
            comment = response.json()

            # Get text and limit to 200 chars
            text = comment.get("text", "")
            # Strip HTML tags (basic cleanup)
            text = re.sub(r"<[^>]+>", "", text)
            return text[:200] if text else None

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
        if not text:
            return None

        for pattern in self.ARXIV_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
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
            "agents": ["agent", "autonomous", "reasoning"],
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
        # 500 points = 100 score (top story threshold)
        return min(100, (raw_score / 500) * 100)
