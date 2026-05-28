"""Embedding generation with multi-tier caching for local-first RAG."""
import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import threading
import numpy as np

from sentence_transformers import SentenceTransformer
from src.config import get_settings
from src.logger import get_logger
from src.exceptions import EmbeddingError


logger = get_logger(__name__)


class MemoryEmbeddingCache:
    """L1 Cache: In-memory LRU cache with TTL for embeddings."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """Initialize memory cache with size and TTL limits.

        Args:
            max_size: Maximum number of embeddings to cache
            ttl: Time-to-live in seconds (0 = no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()  # text_hash -> (embedding, timestamp)
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

        logger.msg(
            "memory_cache_init",
            max_size=max_size,
            ttl=ttl
        )

    def get(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache with TTL check."""
        text_hash = hashlib.md5(text.encode()).hexdigest()

        with self.lock:
            if text_hash not in self.cache:
                self.misses += 1
                return None

            embedding, timestamp = self.cache[text_hash]

            # Check TTL
            if self.ttl > 0 and time.time() - timestamp > self.ttl:
                del self.cache[text_hash]
                self.misses += 1
                logger.msg("cache_expired", text_hash=text_hash)
                return None

            # Move to end (LRU)
            self.cache.move_to_end(text_hash)
            self.hits += 1
            return embedding

    def set(self, text: str, embedding: np.ndarray) -> None:
        """Store embedding in cache with LRU eviction."""
        text_hash = hashlib.md5(text.encode()).hexdigest()

        with self.lock:
            # Remove old entry if exists
            if text_hash in self.cache:
                del self.cache[text_hash]

            # Add new entry
            self.cache[text_hash] = (embedding.copy(), time.time())

            # Evict if over capacity
            if len(self.cache) > self.max_size:
                evicted = self.cache.popitem(last=False)
                logger.msg("cache_evicted", text_hash=evicted[0])

    def clear(self) -> None:
        """Clear all cached embeddings."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
        logger.msg("memory_cache_cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                "type": "memory",
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%",
                "ttl": self.ttl
            }


class DiskEmbeddingCache:
    """L2 Cache: Disk-based persistent cache for embeddings."""

    def __init__(self, cache_dir: str = "/data/cache", max_size_mb: int = 500):
        """Initialize disk cache.

        Args:
            cache_dir: Directory for cache storage
            max_size_mb: Maximum cache size in megabytes
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

        logger.msg(
            "disk_cache_init",
            cache_dir=str(self.cache_dir),
            max_size_mb=max_size_mb
        )

    def _get_cache_path(self, text_hash: str) -> Path:
        """Get cache file path for text hash."""
        # Organize into subdirectories by first 2 chars
        subdir = self.cache_dir / text_hash[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{text_hash}.json"

    def get(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from disk cache."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_path = self._get_cache_path(text_hash)

        with self.lock:
            if not cache_path.exists():
                self.misses += 1
                return None

            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    embedding = np.array(data['embedding'], dtype=np.float32)
                    self.hits += 1
                    return embedding
            except Exception as e:
                logger.msg(
                    "disk_cache_read_error",
                    text_hash=text_hash,
                    error=str(e)
                )
                self.misses += 1
                return None

    def set(self, text: str, embedding: np.ndarray) -> None:
        """Store embedding to disk cache."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_path = self._get_cache_path(text_hash)

        with self.lock:
            try:
                data = {
                    'text_hash': text_hash,
                    'embedding': embedding.tolist(),
                    'created_at': datetime.now().isoformat(),
                    'dims': len(embedding)
                }
                with open(cache_path, 'w') as f:
                    json.dump(data, f)
            except Exception as e:
                logger.msg(
                    "disk_cache_write_error",
                    text_hash=text_hash,
                    error=str(e)
                )

    def clear(self) -> None:
        """Clear all cached files."""
        with self.lock:
            import shutil
            try:
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.hits = 0
                self.misses = 0
                logger.msg("disk_cache_cleared")
            except Exception as e:
                logger.msg("disk_cache_clear_error", error=str(e))

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            total_size = sum(
                f.stat().st_size for f in self.cache_dir.rglob('*.json')
            ) / (1024 * 1024)  # Convert to MB
        except:
            total_size = 0

        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                "type": "disk",
                "size_mb": f"{total_size:.2f}",
                "max_size_mb": self.max_size_mb,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%"
            }


class EmbeddingGenerator:
    """Generate embeddings with multi-tier caching (L1 memory, L2 disk)."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "auto",
        batch_size: int = 32,
        cache_l1: Optional[MemoryEmbeddingCache] = None,
        cache_l2: Optional[DiskEmbeddingCache] = None
    ):
        """Initialize embedding generator.

        Args:
            model_name: SentenceTransformer model name
            device: Device to use ('auto', 'cpu', 'cuda')
            batch_size: Batch size for embedding generation
            cache_l1: Optional L1 memory cache
            cache_l2: Optional L2 disk cache
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.cache_l1 = cache_l1
        self.cache_l2 = cache_l2
        self.device = self._select_device(device)

        try:
            self.model = SentenceTransformer(
                model_name,
                device=self.device
            )
            logger.msg(
                "embedding_generator_init",
                model=model_name,
                device=self.device,
                cache_l1=cache_l1 is not None,
                cache_l2=cache_l2 is not None
            )
        except Exception as e:
            logger.msg(
                "embedding_generator_error",
                error=str(e)
            )
            raise EmbeddingError(f"Failed to load model {model_name}: {e}")

    def _select_device(self, device: str) -> str:
        """Auto-select best available device."""
        if device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
            except:
                device = "cpu"
        return device

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for single text."""
        # Try cache first
        embedding = self._get_from_cache(text)
        if embedding is not None:
            return embedding

        # Generate
        try:
            embedding = self.model.encode(
                text,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            embedding = embedding.astype(np.float32)

            # Store in caches
            self._set_in_cache(text, embedding)

            return embedding
        except Exception as e:
            logger.msg(
                "embedding_generation_error",
                error=str(e)
            )
            raise EmbeddingError(f"Failed to generate embedding: {e}")

    def embed_batch(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[np.ndarray]:
        """Generate embeddings for batch of texts with cache-aware batching."""
        if not texts:
            return []

        embeddings = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        # Separate cached from uncached
        for i, text in enumerate(texts):
            if use_cache:
                embedding = self._get_from_cache(text)
                if embedding is not None:
                    embeddings[i] = embedding
                    continue

            uncached_indices.append(i)
            uncached_texts.append(text)

        # Generate uncached in batches
        if uncached_texts:
            try:
                batch_embeddings = self.model.encode(
                    uncached_texts,
                    batch_size=self.batch_size,
                    normalize_embeddings=True,
                    convert_to_numpy=True
                )
                batch_embeddings = batch_embeddings.astype(np.float32)

                # Store in caches
                for text, embedding in zip(uncached_texts, batch_embeddings):
                    self._set_in_cache(text, embedding)

                # Populate results
                for idx, embedding in zip(uncached_indices, batch_embeddings):
                    embeddings[idx] = embedding

            except Exception as e:
                logger.msg(
                    "batch_embedding_error",
                    count=len(uncached_texts),
                    error=str(e)
                )
                raise EmbeddingError(f"Failed to generate batch embeddings: {e}")

        return embeddings

    def _get_from_cache(self, text: str) -> Optional[np.ndarray]:
        """Try to get embedding from cache hierarchy."""
        # L1: Memory cache
        if self.cache_l1:
            if embedding := self.cache_l1.get(text):
                return embedding

        # L2: Disk cache
        if self.cache_l2:
            if embedding := self.cache_l2.get(text):
                # Promote to L1
                if self.cache_l1:
                    self.cache_l1.set(text, embedding)
                return embedding

        return None

    def _set_in_cache(self, text: str, embedding: np.ndarray) -> None:
        """Store embedding in cache hierarchy."""
        # Store in L2 first (persistent)
        if self.cache_l2:
            self.cache_l2.set(text, embedding)

        # Then in L1 (fast)
        if self.cache_l1:
            self.cache_l1.set(text, embedding)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics from all caches."""
        stats = {
            "model": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size,
            "caches": {}
        }

        if self.cache_l1:
            stats["caches"]["l1_memory"] = self.cache_l1.stats()

        if self.cache_l2:
            stats["caches"]["l2_disk"] = self.cache_l2.stats()

        return stats

    def clear_caches(self) -> None:
        """Clear all caches."""
        if self.cache_l1:
            self.cache_l1.clear()
        if self.cache_l2:
            self.cache_l2.clear()
        logger.msg("all_caches_cleared")
