"""Tests for embedding generation with multi-tier caching."""
import pytest
import tempfile
import shutil
import numpy as np
from pathlib import Path
import time

from src.embeddings import (
    MemoryEmbeddingCache,
    DiskEmbeddingCache,
    EmbeddingGenerator
)
from src.exceptions import EmbeddingError


class TestMemoryEmbeddingCache:
    """Test in-memory L1 cache."""

    @pytest.fixture
    def cache(self):
        """Create cache instance."""
        return MemoryEmbeddingCache(max_size=3, ttl=1)

    def test_cache_init(self, cache):
        """Test cache initialization."""
        assert cache.max_size == 3
        assert cache.ttl == 1
        assert len(cache.cache) == 0

    def test_cache_get_set(self, cache):
        """Test basic get/set operations."""
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        cache.set("test", embedding)

        retrieved = cache.get("test")
        assert retrieved is not None
        np.testing.assert_array_almost_equal(retrieved, embedding)

    def test_cache_hit_miss_tracking(self, cache):
        """Test hit/miss statistics."""
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        cache.set("test", embedding)

        # Cache hit
        cache.get("test")
        assert cache.hits == 1

        # Cache miss
        cache.get("nonexistent")
        assert cache.misses == 1

    def test_cache_ttl_expiration(self, cache):
        """Test TTL-based expiration."""
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        cache.set("test", embedding)

        # Should be available
        assert cache.get("test") is not None

        # Wait for TTL to expire
        time.sleep(1.1)

        # Should be expired
        assert cache.get("test") is None

    def test_cache_max_size_eviction(self, cache):
        """Test LRU eviction when max size exceeded."""
        emb1 = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        emb2 = np.array([0.4, 0.5, 0.6], dtype=np.float32)
        emb3 = np.array([0.7, 0.8, 0.9], dtype=np.float32)
        emb4 = np.array([1.0, 1.1, 1.2], dtype=np.float32)

        cache.set("a", emb1)
        cache.set("b", emb2)
        cache.set("c", emb3)
        assert len(cache.cache) == 3

        # Adding 4th should evict first
        cache.set("d", emb4)
        assert len(cache.cache) == 3
        assert cache.get("a") is None

    def test_cache_clear(self, cache):
        """Test clearing cache."""
        cache.set("test", np.array([0.1, 0.2], dtype=np.float32))
        assert len(cache.cache) > 0

        cache.clear()
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set("test", np.array([0.1, 0.2], dtype=np.float32))
        cache.get("test")
        cache.get("nonexistent")

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert "hit_rate" in stats
        assert stats["type"] == "memory"


class TestDiskEmbeddingCache:
    """Test disk-based L2 cache."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache(self, temp_dir):
        """Create disk cache instance."""
        return DiskEmbeddingCache(cache_dir=temp_dir, max_size_mb=100)

    def test_cache_init(self, cache):
        """Test cache initialization."""
        assert cache.cache_dir.exists()
        assert cache.max_size_mb == 100

    def test_cache_persistence(self, cache, temp_dir):
        """Test cache survives across instances."""
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        cache.set("test", embedding)

        # Create new cache instance
        cache2 = DiskEmbeddingCache(cache_dir=temp_dir)
        retrieved = cache2.get("test")

        assert retrieved is not None
        np.testing.assert_array_almost_equal(retrieved, embedding)

    def test_cache_get_set(self, cache):
        """Test get/set operations."""
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        cache.set("test", embedding)

        retrieved = cache.get("test")
        assert retrieved is not None

    def test_cache_miss(self, cache):
        """Test cache miss."""
        assert cache.get("nonexistent") is None

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set("test", np.array([0.1, 0.2], dtype=np.float32))
        cache.get("test")
        cache.get("nonexistent")

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["type"] == "disk"

    def test_cache_clear(self, cache, temp_dir):
        """Test clearing cache."""
        cache.set("test", np.array([0.1, 0.2], dtype=np.float32))
        assert (Path(temp_dir) / "te").exists()

        cache.clear()
        assert len(list(Path(temp_dir).glob("**/*.json"))) == 0


class TestEmbeddingGenerator:
    """Test embedding generator with caching."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create generator with caches."""
        l1_cache = MemoryEmbeddingCache(max_size=10)
        l2_cache = DiskEmbeddingCache(cache_dir=temp_dir)
        return EmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            batch_size=2,
            cache_l1=l1_cache,
            cache_l2=l2_cache
        )

    def test_generator_init(self, generator):
        """Test generator initialization."""
        assert generator.model is not None
        assert generator.cache_l1 is not None
        assert generator.cache_l2 is not None
        assert generator.batch_size == 2

    def test_single_embedding(self, generator):
        """Test generating single embedding."""
        embedding = generator.embed_text("Hello world")

        assert embedding is not None
        assert len(embedding) == 384  # MiniLM-L6-v2 embedding size
        assert embedding.dtype == np.float32

    def test_batch_embedding(self, generator):
        """Test generating batch of embeddings."""
        texts = ["Hello", "World", "Test"]
        embeddings = generator.embed_batch(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 384
            assert emb.dtype == np.float32

    def test_cache_hit_single(self, generator):
        """Test cache hit for single text."""
        # First call - generate
        generator.embed_text("Hello world")

        # Second call - from cache
        embedding = generator.embed_text("Hello world")
        assert embedding is not None

        # Check cache stats
        stats = generator.get_cache_stats()
        assert stats["caches"]["l1_memory"]["hits"] >= 1

    def test_cache_hit_batch(self, generator):
        """Test cache hits in batch processing."""
        texts = ["Hello", "World"]

        # First batch - all generated
        generator.embed_batch(texts)

        # Second batch - all from cache
        embeddings = generator.embed_batch(texts)

        assert len(embeddings) == 2
        for emb in embeddings:
            assert emb is not None

    def test_cache_hit_cross_tier(self, generator):
        """Test L2 to L1 promotion."""
        text = "Test text"

        # Generate
        generator.embed_text(text)

        # Clear L1 cache
        generator.cache_l1.clear()

        # Retrieve from L2 and promote to L1
        embedding = generator.embed_text(text)
        assert embedding is not None

    def test_batch_with_cache(self, generator):
        """Test batch processing with mixed cached/uncached."""
        # Cache some texts
        generator.embed_text("Cached 1")
        generator.embed_text("Cached 2")

        # Batch with cached and uncached
        texts = ["Cached 1", "Cached 2", "New 1", "New 2"]
        embeddings = generator.embed_batch(texts)

        assert len(embeddings) == 4
        for emb in embeddings:
            assert emb is not None

    def test_empty_batch(self, generator):
        """Test empty batch handling."""
        embeddings = generator.embed_batch([])
        assert embeddings == []

    def test_cache_stats(self, generator):
        """Test cache statistics."""
        generator.embed_text("Hello")
        generator.embed_batch(["World", "Test"])

        stats = generator.get_cache_stats()
        assert "model" in stats
        assert "device" in stats
        assert "caches" in stats
        assert "l1_memory" in stats["caches"]
        assert "l2_disk" in stats["caches"]

    def test_clear_caches(self, generator):
        """Test clearing all caches."""
        generator.embed_text("Hello")
        assert generator.cache_l1.hits > 0

        generator.clear_caches()
        assert generator.cache_l1.hits == 0
        assert generator.cache_l2.hits == 0

    def test_generator_without_caches(self):
        """Test generator without caches."""
        generator = EmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_l1=None,
            cache_l2=None
        )

        embedding = generator.embed_text("Hello")
        assert embedding is not None

    def test_batch_normalization(self, generator):
        """Test that embeddings are normalized."""
        text = "Test"
        embedding = generator.embed_text(text)

        # Check normalization (should have unit norm)
        norm = np.linalg.norm(embedding)
        np.testing.assert_almost_equal(norm, 1.0, decimal=5)

    def test_invalid_model(self):
        """Test error handling for invalid model."""
        with pytest.raises(EmbeddingError):
            EmbeddingGenerator(model_name="invalid-model-name-xyz")


class TestMultiTierCaching:
    """Test multi-tier caching integration."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create generator with both caches."""
        l1 = MemoryEmbeddingCache(max_size=5)
        l2 = DiskEmbeddingCache(cache_dir=temp_dir)
        return EmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_l1=l1,
            cache_l2=l2
        )

    def test_fallthrough_cache_l1_hit(self, generator):
        """Test L1 cache hit (fastest)."""
        text = "Test"
        generator.embed_text(text)

        # Get from L1
        embedding = generator.embed_text(text)
        assert embedding is not None
        assert generator.cache_l1.hits >= 1

    def test_fallthrough_cache_l2_hit(self, generator, temp_dir):
        """Test L1 miss, L2 hit (promotes to L1)."""
        text = "Test text"
        generator.embed_text(text)

        # Clear L1
        generator.cache_l1.clear()

        # Should hit L2
        embedding = generator.embed_text(text)
        assert embedding is not None

        # Should now be in L1
        assert generator.embed_text(text) is not None

    def test_comprehensive_caching_stats(self, generator):
        """Test comprehensive cache statistics."""
        # Generate embeddings
        for i in range(5):
            generator.embed_text(f"Text {i}")

        # Access some multiple times
        for i in range(3):
            generator.embed_text(f"Text 0")

        # Get stats
        stats = generator.get_cache_stats()

        assert stats["caches"]["l1_memory"]["hits"] > 0
        assert stats["caches"]["l2_disk"]["hits"] >= 0

    def test_cache_no_duplicate_storage(self, generator):
        """Test that same text isn't stored multiple times."""
        text = "Duplicate test"

        generator.embed_text(text)
        generator.embed_text(text)
        generator.embed_text(text)

        # Should only be stored once per cache
        l1_stats = generator.cache_l1.stats()
        l2_stats = generator.cache_l2.stats()

        assert l1_stats["size"] == 1  # Only one unique embedding
