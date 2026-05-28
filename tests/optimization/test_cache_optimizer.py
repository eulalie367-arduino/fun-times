"""Tests for smart cache optimizer."""

import pytest
import time
from src.optimization.cache_optimizer import SmartCache, CacheEntry


class TestSmartCache:
    """Test smart cache functionality."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = SmartCache(max_size_mb=100, ttl_seconds=3600)

        assert cache.max_size_bytes == 100 * 1024 * 1024
        assert cache.ttl_seconds == 3600
        assert len(cache.cache) == 0
        assert cache.current_size_bytes == 0

    def test_put_and_get(self):
        """Test basic put and get operations."""
        cache = SmartCache(max_size_mb=100)

        cache.put("key1", "value1", size_bytes=100)
        result = cache.get("key1")

        assert result == "value1"
        assert cache.access_stats['hits'] == 1
        assert cache.access_stats['misses'] == 0

    def test_cache_miss(self):
        """Test cache miss."""
        cache = SmartCache(max_size_mb=100)

        result = cache.get("nonexistent")

        assert result is None
        assert cache.access_stats['misses'] == 1

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = SmartCache(max_size_mb=100, ttl_seconds=1)

        cache.put("key", "value", size_bytes=100)
        time.sleep(1.1)

        result = cache.get("key")

        assert result is None

    def test_cache_eviction(self):
        """Test automatic eviction when full."""
        cache = SmartCache(max_size_mb=0.001)  # Very small cache

        cache.put("key1", "x" * 100, size_bytes=100)
        cache.put("key2", "y" * 100, size_bytes=100)
        cache.put("key3", "z" * 100, size_bytes=100)

        # First entries should be evicted
        assert cache.access_stats['evictions'] > 0

    def test_access_count_increase(self):
        """Test that access count increases."""
        cache = SmartCache(max_size_mb=100)

        cache.put("key", "value", size_bytes=100)
        cache.get("key")
        cache.get("key")

        entry = cache.cache["key"]
        assert entry.access_count == 3

    def test_score_calculation(self):
        """Test utility score calculation."""
        cache = SmartCache(max_size_mb=100)

        entry = CacheEntry(
            key="test",
            value="value",
            access_count=10,
            creation_time=time.time(),
            last_access_time=time.time(),
            size_bytes=1024,
            score=0.0
        )

        score = cache._calculate_score(entry)

        assert 0 <= score <= 1

    def test_clear_expired(self):
        """Test clearing expired entries."""
        cache = SmartCache(max_size_mb=100, ttl_seconds=1)

        cache.put("key1", "value1", size_bytes=100)
        cache.put("key2", "value2", size_bytes=100)
        time.sleep(1.1)

        cleared = cache.clear_expired()

        assert cleared == 2
        assert len(cache.cache) == 0

    def test_get_stats(self):
        """Test statistics retrieval."""
        cache = SmartCache(max_size_mb=100)

        cache.put("key1", "value1", size_bytes=100)
        cache.get("key1")
        cache.get("nonexistent")

        stats = cache.get_stats()

        assert "hit_rate" in stats
        assert "size_mb" in stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cache_update_entry(self):
        """Test updating an existing cache entry."""
        cache = SmartCache(max_size_mb=100)

        cache.put("key", "value1", size_bytes=100)
        cache.put("key", "value2", size_bytes=100)

        result = cache.get("key")

        assert result == "value2"
        assert len(cache.cache) == 1

    def test_size_estimate(self):
        """Test that cache size tracking works."""
        cache = SmartCache(max_size_mb=100)

        cache.put("key1", "value1", size_bytes=1000)
        cache.put("key2", "value2", size_bytes=2000)

        stats = cache.get_stats()

        assert stats["size_mb"] > 0
        assert stats["entries"] == 2
