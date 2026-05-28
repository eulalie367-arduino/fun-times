"""Search analytics and performance tracking.

Tracks search queries, performance, and user behavior patterns.
"""

from typing import Dict, List, Tuple, Any
import logging
from dataclasses import dataclass
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SearchEvent:
    """Represents a search event."""
    query: str
    timestamp: float
    duration_ms: float
    num_results: int
    result_clicked: bool = False
    clicked_rank: int = -1


class SearchAnalytics:
    """Track and analyze search usage."""

    def __init__(self):
        """Initialize search analytics."""
        self.events: List[SearchEvent] = []
        self.performance_metrics = {
            'total_searches': 0,
            'total_clicks': 0,
            'avg_duration_ms': 0.0
        }
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                'count': 0,
                'total_duration_ms': 0.0,
                'clicks': 0,
                'avg_click_rank': 0
            }
        )

    def record_search(
        self,
        query: str,
        duration_ms: float,
        num_results: int
    ) -> None:
        """Record a search event.

        Args:
            query: Query string
            duration_ms: Query execution time in milliseconds
            num_results: Number of results returned
        """
        event = SearchEvent(
            query=query,
            timestamp=time.time(),
            duration_ms=duration_ms,
            num_results=num_results
        )

        self.events.append(event)

        # Update metrics
        self.performance_metrics['total_searches'] += 1
        total_duration = self.performance_metrics['total_searches']
        avg_so_far = self.performance_metrics['avg_duration_ms']

        self.performance_metrics['avg_duration_ms'] = (
            (avg_so_far * (total_duration - 1) + duration_ms) / total_duration
        )

        # Update query stats
        query_lower = query.lower()
        self.query_stats[query_lower]['count'] += 1
        self.query_stats[query_lower]['total_duration_ms'] += duration_ms

    def record_click(self, query: str, rank: int) -> None:
        """Record a user click on search result.

        Args:
            query: Query that was searched
            rank: Rank of clicked result (0-based)
        """
        query_lower = query.lower()

        # Update last event for this query
        for event in reversed(self.events):
            if event.query == query_lower and not event.result_clicked:
                event.result_clicked = True
                event.clicked_rank = rank
                break

        # Update metrics
        self.performance_metrics['total_clicks'] += 1
        self.query_stats[query_lower]['clicks'] += 1

        if self.query_stats[query_lower]['count'] > 0:
            avg_rank = (
                (self.query_stats[query_lower]['avg_click_rank'] *
                 (self.query_stats[query_lower]['clicks'] - 1) + rank)
                / self.query_stats[query_lower]['clicks']
            )
            self.query_stats[query_lower]['avg_click_rank'] = avg_rank

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics.

        Returns:
            Dictionary with performance statistics
        """
        click_through_rate = 0.0
        if self.performance_metrics['total_searches'] > 0:
            click_through_rate = (
                self.performance_metrics['total_clicks']
                / self.performance_metrics['total_searches']
            )

        return {
            'total_searches': self.performance_metrics['total_searches'],
            'total_clicks': self.performance_metrics['total_clicks'],
            'click_through_rate': click_through_rate,
            'avg_duration_ms': self.performance_metrics['avg_duration_ms']
        }

    def get_query_metrics(self, query: str) -> Dict[str, Any]:
        """Get metrics for a specific query.

        Args:
            query: Query string

        Returns:
            Dictionary with query statistics
        """
        query_lower = query.lower()

        if query_lower not in self.query_stats:
            return {}

        stats = self.query_stats[query_lower]

        return {
            'query': query,
            'count': stats['count'],
            'avg_duration_ms': (
                stats['total_duration_ms'] / stats['count']
                if stats['count'] > 0 else 0
            ),
            'clicks': stats['clicks'],
            'ctr': stats['clicks'] / stats['count'] if stats['count'] > 0 else 0,
            'avg_click_rank': stats['avg_click_rank']
        }

    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently searched queries.

        Args:
            limit: Maximum number of queries

        Returns:
            List of top query metrics
        """
        sorted_queries = sorted(
            self.query_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        return [
            self.get_query_metrics(query)
            for query, _ in sorted_queries[:limit]
        ]

    def get_slowest_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest queries by average duration.

        Args:
            limit: Maximum number of queries

        Returns:
            List of slowest query metrics
        """
        sorted_queries = sorted(
            self.query_stats.items(),
            key=lambda x: x[1]['total_duration_ms'] / max(x[1]['count'], 1),
            reverse=True
        )

        return [
            self.get_query_metrics(query)
            for query, _ in sorted_queries[:limit]
        ]

    def get_engagement_metrics(self) -> Dict[str, float]:
        """Get user engagement metrics.

        Returns:
            Dictionary with engagement statistics
        """
        if not self.events:
            return {}

        clicked_events = sum(1 for e in self.events if e.result_clicked)
        avg_rank_when_clicked = 0.0

        if clicked_events > 0:
            total_rank = sum(
                e.clicked_rank for e in self.events if e.result_clicked
            )
            avg_rank_when_clicked = total_rank / clicked_events

        return {
            'total_events': len(self.events),
            'clicked_events': clicked_events,
            'engagement_rate': clicked_events / len(self.events) if self.events else 0,
            'avg_click_rank': avg_rank_when_clicked
        }
