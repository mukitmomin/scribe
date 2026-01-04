"""
Abstract base class for trend sources.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import re

from .models import TrendSignal


class TrendSource(ABC):
    """
    Abstract base class for all trend sources.

    Each source (HackerNews, Reddit, etc.) implements this interface to provide
    a consistent way to fetch trending papers from different platforms.
    """

    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize the trend source.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, List[TrendSignal]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

    @abstractmethod
    async def fetch_trending(
        self,
        topic: str = "AI",
        time_window_hours: int = 168,
        max_results: int = 50,
    ) -> List[TrendSignal]:
        """
        Fetch trending papers from this source.

        Args:
            topic: Topic to search for (e.g., "AI", "LLM", "ML")
            time_window_hours: How far back to look (default: 1 week)
            max_results: Maximum number of signals to return

        Returns:
            List of TrendSignal objects representing mentions of papers
        """
        pass

    @abstractmethod
    def extract_paper_id(self, text: str) -> Optional[str]:
        """
        Extract arXiv paper ID from URL or text.

        Should handle various formats:
        - https://arxiv.org/abs/2401.12345
        - https://arxiv.org/pdf/2401.12345.pdf
        - arxiv:2401.12345
        - [2401.12345]

        Args:
            text: URL or text containing arXiv reference

        Returns:
            arXiv ID (e.g., "2401.12345") or None if not found
        """
        pass

    def compute_engagement_score(self, signal: TrendSignal) -> float:
        """
        Compute normalized engagement score for a signal.

        Default formula: upvotes + (comments * 2) + (shares * 3)
        Subclasses can override for platform-specific scoring.

        Args:
            signal: TrendSignal object with engagement metrics

        Returns:
            Engagement score (0-100, normalized)
        """
        raw_score = signal.upvotes + (signal.comments * 2) + (signal.shares * 3)

        # Normalize to 0-100 scale
        # Divisor can be adjusted based on typical platform engagement
        return min(100, raw_score / 10)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache_timestamps:
            return False

        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
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

    def _extract_arxiv_id_patterns(self, text: str) -> Optional[str]:
        """
        Common arXiv ID extraction patterns.

        Subclasses can use or override this method.
        """
        patterns = [
            r"arxiv\.org/abs/(\d{4}\.\d{4,5})",
            r"arxiv\.org/pdf/(\d{4}\.\d{4,5})",
            r"arxiv:(\d{4}\.\d{4,5})",
            r"\[(\d{4}\.\d{4,5})\]",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None
