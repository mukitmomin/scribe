"""
Trend Discovery Service

Multi-source trend aggregation for discovering trending AI/ML research papers
based on social media buzz, expert discussions, and community engagement.
"""

from .models import TrendSignal, TrendingPaper
from .base import TrendSource
from .aggregator import TrendAggregator

__all__ = [
    "TrendSignal",
    "TrendingPaper",
    "TrendSource",
    "TrendAggregator",
]
