"""Smart cache optimization with weighted LRU eviction.

Optimizes cache memory by removing low-utility entries based on multiple factors.
"""

from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    key: str
    value: Any
    access_count: int = 0
    last_access_time: float = 0.0
    creation_time: float = 0.0
    size_bytes: int = 0
    score: float = 0.0


class SmartCache:
    """LRU cache with weighted eviction based on utility scores."""

    def __init__(
        self,
        max_size_mb: float = 150.0,
        ttl_seconds: int = 1800,
        min_score_threshold: float = 0.1
    ):
        """Initialize smart cache.

        Args:
            max_size_mb: Maximum cache size in MB
            ttl_seconds: Time-to-live for cache entries (30 minutes default)
            min_score_threshold: Minimum score to keep entry (0-1 range)
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.ttl_seconds = ttl_seconds
        self.min_score_threshold = min_score_threshold
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_size_bytes = 0
        self.access_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache and update access metadata.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            self.access_stats['misses'] += 1
            return None

        entry = self.cache[key]

        # Check if expired
        if time.time() - entry.creation_time > self.ttl_seconds:
            self._remove_entry(key)
            self.access_stats['misses'] += 1
            return None

        # Update access metadata
        entry.access_count += 1
        entry.last_access_time = time.time()
        entry.score = self._calculate_score(entry)

        # Move to end (most recently used)
        self.cache.move_to_end(key)

        self.access_stats['hits'] += 1
        return entry.value

    def put(self, key: str, value: Any, size_bytes: Optional[int] = None) -> None:
        """Put value in cache with automatic eviction if needed.

        Args:
            key: Cache key
            value: Value to cache
            size_bytes: Estimated size in bytes (auto-calculated if not provided)
        """
        if size_bytes is None:
            size_bytes = self._estimate_size(value)

        # Remove old entry if it exists
        if key in self.cache:
            self.current_size_bytes -= self.cache[key].size_bytes

        # Create new entry
        now = time.time()
        entry = CacheEntry(
            key=key,
            value=value,
            access_count=1,
            last_access_time=now,
            creation_time=now,
            size_bytes=size_bytes,
            score=0.0
        )

        self.cache[key] = entry
        self.current_size_bytes += size_bytes

        # Evict low-score entries if needed
        while self.current_size_bytes > self.max_size_bytes and len(self.cache) > 1:
            self._evict_lowest_score()

    def _calculate_score(self, entry: CacheEntry) -> float:
        """Calculate utility score for cache entry.

        Combines: recency, frequency, and size factors.

        Args:
            entry: Cache entry

        Returns:
            Score between 0 and 1 (higher is better)
        """
        now = time.time()

        # Recency factor (0-1): how recently accessed
        recency = 1.0 - min(
            (now - entry.last_access_time) / self.ttl_seconds, 1.0
        )

        # Frequency factor (0-1): normalized access count
        frequency = min(entry.access_count / 100.0, 1.0)

        # Size penalty: prefer smaller entries
        size_penalty = min(entry.size_bytes / (1024 * 1024), 1.0)

        # Combined score with weights
        score = (0.4 * recency + 0.4 * frequency) * (1.0 - 0.2 * size_penalty)

        return float(score)

    def _evict_lowest_score(self) -> None:
        """Evict entry with lowest utility score."""
        if not self.cache:
            return

        # Calculate scores for all entries
        scores = [
            (key, self._calculate_score(entry))
            for key, entry in self.cache.items()
        ]

        # Find lowest score
        lowest_key, lowest_score = min(scores, key=lambda x: x[1])

        # Only evict if below threshold
        if lowest_score < self.min_score_threshold:
            self._remove_entry(lowest_key)
            self.access_stats['evictions'] += 1
            logger.debug(f"Evicted cache entry {lowest_key} (score: {lowest_score:.2f})")

    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self.cache:
            entry = self.cache[key]
            self.current_size_bytes -= entry.size_bytes
            del self.cache[key]

    def clear_expired(self) -> int:
        """Remove all expired entries. Returns number removed."""
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry.creation_time > self.ttl_seconds
        ]

        for key in expired_keys:
            self._remove_entry(key)

        logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with hit rate, size info, etc.
        """
        total_accesses = self.access_stats['hits'] + self.access_stats['misses']
        hit_rate = (
            self.access_stats['hits'] / total_accesses
            if total_accesses > 0 else 0.0
        )

        return {
            'size_mb': self.current_size_bytes / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'entries': len(self.cache),
            'hit_rate': hit_rate,
            'hits': self.access_stats['hits'],
            'misses': self.access_stats['misses'],
            'evictions': self.access_stats['evictions']
        }

    @staticmethod
    def _estimate_size(obj: Any) -> int:
        """Estimate object size in bytes."""
        import sys
        return sys.getsizeof(obj)
