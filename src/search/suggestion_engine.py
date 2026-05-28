"""Query suggestion and autocomplete engine.

Provides suggestions for user queries based on frequency and recency.
"""

from typing import List, Dict, Tuple, Optional
import logging
from collections import defaultdict, Counter
import time

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """Generate query suggestions."""

    def __init__(self, max_suggestions: int = 10):
        """Initialize suggestion engine.

        Args:
            max_suggestions: Maximum suggestions to return
        """
        self.max_suggestions = max_suggestions
        self.query_history: List[Tuple[str, float]] = []  # (query, timestamp)
        self.query_frequency: Counter = Counter()
        self.prefix_index: Dict[str, List[str]] = defaultdict(list)

    def record_query(self, query: str):
        """Record a user query.

        Args:
            query: Query string
        """
        query_lower = query.lower()
        timestamp = time.time()

        self.query_history.append((query_lower, timestamp))
        self.query_frequency[query_lower] += 1

        # Index by prefix
        for i in range(1, len(query_lower) + 1):
            prefix = query_lower[:i]
            if query_lower not in self.prefix_index[prefix]:
                self.prefix_index[prefix].append(query_lower)

        logger.debug(f"Recorded query: {query}")

    def get_suggestions(
        self,
        prefix: str,
        limit: Optional[int] = None
    ) -> List[str]:
        """Get suggestions for a prefix.

        Args:
            prefix: Query prefix
            limit: Maximum suggestions (uses default if None)

        Returns:
            List of suggested queries
        """
        limit = limit or self.max_suggestions
        prefix_lower = prefix.lower()

        if prefix_lower not in self.prefix_index:
            return []

        candidates = self.prefix_index[prefix_lower]

        # Rank by frequency
        ranked = sorted(
            candidates,
            key=lambda q: self.query_frequency[q],
            reverse=True
        )

        return ranked[:limit]

    def get_trending(self, hours: int = 24, limit: Optional[int] = None) -> List[str]:
        """Get trending queries.

        Args:
            hours: Hours to look back
            limit: Maximum results

        Returns:
            List of trending queries
        """
        limit = limit or self.max_suggestions
        cutoff_time = time.time() - (hours * 3600)

        # Count recent queries
        recent_count = Counter()

        for query, timestamp in self.query_history:
            if timestamp > cutoff_time:
                recent_count[query] += 1

        # Return top by frequency
        trending = recent_count.most_common(limit)
        return [query for query, _ in trending]

    def get_related_queries(self, query: str, limit: Optional[int] = None) -> List[str]:
        """Get queries related to a given query.

        Args:
            query: Reference query
            limit: Maximum results

        Returns:
            List of related queries
        """
        limit = limit or self.max_suggestions
        query_lower = query.lower()

        # Find queries with similar terms
        query_words = set(query_lower.split())
        related = []

        for other_query, freq in self.query_frequency.most_common():
            if other_query == query_lower:
                continue

            other_words = set(other_query.split())
            similarity = len(query_words & other_words) / len(query_words | other_words)

            if similarity > 0.3:  # At least 30% similarity
                related.append(other_query)

            if len(related) >= limit:
                break

        return related

    def autocomplete(self, partial_query: str, limit: Optional[int] = None) -> List[str]:
        """Autocomplete a partial query.

        Args:
            partial_query: Partial query string
            limit: Maximum results

        Returns:
            List of autocomplete suggestions
        """
        return self.get_suggestions(partial_query, limit)

    def cleanup_old_queries(self, days: int = 30):
        """Remove old queries from history.

        Args:
            days: Queries older than this many days
        """
        cutoff_time = time.time() - (days * 24 * 3600)

        self.query_history = [
            (q, t) for q, t in self.query_history
            if t > cutoff_time
        ]

        logger.info(f"Cleaned up queries older than {days} days")

    def get_stats(self) -> Dict[str, int]:
        """Get suggestion engine statistics.

        Returns:
            Dictionary with metrics
        """
        return {
            "total_queries": len(self.query_history),
            "unique_queries": len(self.query_frequency),
            "prefixes": len(self.prefix_index)
        }
