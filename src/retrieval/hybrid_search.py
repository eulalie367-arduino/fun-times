"""Hybrid search layer combining sparse (BM25) and dense (vector) retrieval.

Implements:
- Sparse retrieval via BM25
- Dense retrieval via ChromaDB embeddings
- Reciprocal Rank Fusion (RRF) combining both
- Cross-encoder reranking via BGE-Reranker-v2-m3
- Semantic query caching for 60-80% hit rate
"""

import hashlib
import json
import time
import os
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import threading
import numpy as np
from collections import OrderedDict

from src.logger import get_logger
from src.exceptions import RetrievalError, EmbeddingError
from src.config import get_settings

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Single search result with all metadata."""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # 'bm25', 'dense', 'fused', or 'reranked'
    retrieval_rank: int = 0  # Original rank before fusion

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class HybridSearchStats:
    """Statistics from hybrid search operation."""
    query: str
    total_time_ms: float
    cache_hit: bool
    cache_similarity: Optional[float] = None
    bm25_results: int = 0
    dense_results: int = 0
    fused_results: int = 0
    reranked_results: int = 0
    final_results: int = 0


class SemanticQueryCache:
    """Cache query embeddings and results with semantic similarity matching.

    Target: 60-80% hit rate for similar queries.
    TTL: 24 hours per entry.
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 86400,  # 24 hours
        similarity_threshold: float = 0.95
    ):
        """Initialize semantic cache.

        Args:
            max_size: Maximum number of cached queries
            ttl_seconds: Time-to-live in seconds (24 hours default)
            similarity_threshold: Cosine similarity threshold for cache hits
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.similarity_threshold = similarity_threshold
        self.cache = OrderedDict()  # query_hash -> (embedding, results, timestamp)
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

        logger.msg(
            "semantic_cache_init",
            max_size=max_size,
            ttl_seconds=ttl_seconds,
            similarity_threshold=similarity_threshold
        )

    def get(
        self,
        query: str,
        query_embedding: Optional[np.ndarray] = None
    ) -> Optional[List[SearchResult]]:
        """Get cached results via semantic similarity.

        Args:
            query: The query string
            query_embedding: Pre-computed embedding for the query

        Returns:
            Cached results if similarity > threshold, None otherwise
        """
        if query_embedding is None:
            return None

        with self.lock:
            best_match = None
            best_similarity = 0

            # Find most similar cached query
            for cached_query_hash, (cached_embedding, cached_results, timestamp) in self.cache.items():
                # Check TTL
                if time.time() - timestamp > self.ttl_seconds:
                    continue

                # Compute cosine similarity
                similarity = self._cosine_similarity(query_embedding, cached_embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (cached_results, similarity)

            # Return if similarity exceeds threshold
            if best_match and best_similarity >= self.similarity_threshold:
                self.hits += 1
                logger.msg(
                    "semantic_cache_hit",
                    similarity=f"{best_similarity:.4f}",
                    results_count=len(best_match[0])
                )
                return best_match[0]

            self.misses += 1
            return None

    def set(
        self,
        query: str,
        query_embedding: np.ndarray,
        results: List[SearchResult]
    ) -> None:
        """Store query and results in cache.

        Args:
            query: The query string
            query_embedding: Embedding for the query
            results: Search results to cache
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()

        with self.lock:
            # Remove old entry if exists
            if query_hash in self.cache:
                del self.cache[query_hash]

            # Add new entry
            self.cache[query_hash] = (query_embedding.copy(), results, time.time())

            # Evict oldest if over capacity
            if len(self.cache) > self.max_size:
                evicted = self.cache.popitem(last=False)
                logger.msg("semantic_cache_evicted", query_hash=evicted[0])

    def clear(self) -> None:
        """Clear all cached entries."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
        logger.msg("semantic_cache_cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0

            # Count expired entries
            expired_count = 0
            current_time = time.time()
            for _, (_, _, timestamp) in self.cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_count += 1

            return {
                "type": "semantic_query",
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%",
                "expired_entries": expired_count,
                "ttl_seconds": self.ttl_seconds
            }

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))


class BM25Indexer:
    """Sparse retrieval using BM25 algorithm."""

    def __init__(self):
        """Initialize BM25 indexer."""
        try:
            from rank_bm25 import BM25Okapi
            self.BM25Okapi = BM25Okapi
        except ImportError:
            raise RetrievalError(
                "rank_bm25 library required. Install with: pip install rank-bm25"
            )

        self.bm25 = None
        self.documents = []  # List of (doc_id, content, metadata)
        self.doc_texts = []  # Tokenized text for BM25

        logger.msg("bm25_indexer_init")

    def index_documents(
        self,
        documents: List[Tuple[str, str, Dict[str, Any]]]
    ) -> int:
        """Build BM25 index from documents.

        Args:
            documents: List of (doc_id, content, metadata) tuples

        Returns:
            Number of documents indexed
        """
        self.documents = documents
        self.doc_texts = []

        for _, content, _ in documents:
            # Simple tokenization: split on whitespace and lowercase
            tokens = content.lower().split()
            self.doc_texts.append(tokens)

        self.bm25 = self.BM25Okapi(self.doc_texts)

        logger.msg("bm25_index_built", num_documents=len(documents))
        return len(documents)

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search using BM25.

        Args:
            query: Query string
            top_k: Number of top results to return

        Returns:
            List of SearchResult objects
        """
        if self.bm25 is None:
            logger.msg("bm25_search_error", error="Index not built")
            return []

        # Tokenize query
        query_tokens = query.lower().split()

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Sort by score
        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        # Build results
        results = []
        for rank, (idx, score) in enumerate(ranked):
            doc_id, content, metadata = self.documents[idx]
            results.append(SearchResult(
                doc_id=doc_id,
                content=content,
                score=float(score),
                metadata=metadata,
                source="bm25",
                retrieval_rank=rank
            ))

        logger.msg("bm25_search_complete", query_length=len(query), results_count=len(results))
        return results


class CrossEncoderReranker:
    """Rerank search results using cross-encoder model."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        batch_size: int = 32,
        device: str = "auto"
    ):
        """Initialize cross-encoder reranker.

        Args:
            model_name: HuggingFace model identifier
            batch_size: Batch size for reranking
            device: Device to use ('auto', 'cpu', 'cuda')
        """
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name, device=self._select_device(device))
        except ImportError:
            raise RetrievalError(
                "sentence-transformers library required for cross-encoder"
            )

        self.model_name = model_name
        self.batch_size = batch_size

        logger.msg(
            "cross_encoder_init",
            model=model_name,
            device=self._select_device(device)
        )

    @staticmethod
    def _select_device(device: str) -> str:
        """Select best available device."""
        if device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                else:
                    device = "cpu"
            except:
                device = "cpu"
        return device

    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 10
    ) -> List[SearchResult]:
        """Rerank results using cross-encoder.

        Args:
            query: Query string
            results: Initial search results
            top_k: Number of top results to return after reranking

        Returns:
            Reranked results
        """
        if not results:
            return []

        # Prepare pairs for reranking
        pairs = [(query, result.content) for result in results]

        # Get reranking scores
        scores = self.model.predict(pairs)

        # Sort by score
        ranked = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        # Update results with reranking scores
        reranked_results = []
        for rank, (result, score) in enumerate(ranked):
            result.score = float(score)
            result.source = "reranked"
            result.retrieval_rank = rank
            reranked_results.append(result)

        logger.msg(
            "cross_encoder_rerank_complete",
            input_results=len(results),
            output_results=len(reranked_results),
            top_k=top_k
        )
        return reranked_results


class HybridSearcher:
    """Hybrid search combining sparse (BM25) + dense (vector) retrieval.

    Pipeline:
    1. Check semantic query cache (target 60-80% hit rate)
    2. Sparse retrieval (BM25)
    3. Dense retrieval (ChromaDB embeddings)
    4. RRF fusion with configurable alpha
    5. Cross-encoder reranking
    6. Return top-k results
    """

    def __init__(
        self,
        vector_store,
        embedding_generator,
        collection_name: str = "documents",
        bm25_indexer: Optional[BM25Indexer] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        semantic_cache: Optional[SemanticQueryCache] = None,
        rrf_k: int = 60,
        rrf_alpha: float = 0.5
    ):
        """Initialize hybrid searcher.

        Args:
            vector_store: ChromaDB vector store instance
            embedding_generator: Embedding generator with caching
            collection_name: ChromaDB collection name
            bm25_indexer: BM25 indexer (created if not provided)
            reranker: Cross-encoder reranker (lazy loaded if not provided)
            semantic_cache: Semantic query cache (created if not provided)
            rrf_k: RRF parameter k (default 60)
            rrf_alpha: Weight for RRF fusion (0.5 = equal weight)
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.collection_name = collection_name
        self.rrf_k = rrf_k
        self.rrf_alpha = rrf_alpha

        self.bm25_indexer = bm25_indexer or BM25Indexer()
        self._reranker = reranker
        self._reranker_lazy_loaded = False

        self.semantic_cache = semantic_cache or SemanticQueryCache()

        logger.msg(
            "hybrid_searcher_init",
            collection=collection_name,
            rrf_k=rrf_k,
            rrf_alpha=rrf_alpha
        )

    @property
    def reranker(self) -> CrossEncoderReranker:
        """Lazy load cross-encoder reranker on first use."""
        if self._reranker is None and not self._reranker_lazy_loaded:
            try:
                self._reranker = CrossEncoderReranker()
                self._reranker_lazy_loaded = True
            except Exception as e:
                logger.msg(
                    "cross_encoder_lazy_load_error",
                    error=str(e)
                )
                raise RetrievalError(f"Failed to load cross-encoder: {e}")
        return self._reranker

    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        field_content: str = "content",
        field_id: str = "id"
    ) -> Dict[str, Any]:
        """Index documents for hybrid search.

        Args:
            documents: List of document dictionaries
            field_content: Field name containing document content
            field_id: Field name containing document ID

        Returns:
            Indexing statistics
        """
        try:
            # Prepare for BM25
            bm25_docs = []
            for doc in documents:
                doc_id = doc.get(field_id, hashlib.md5(
                    str(doc).encode()).hexdigest()[:8])
                content = doc.get(field_content, "")
                metadata = {k: v for k, v in doc.items()
                           if k not in [field_id, field_content]}
                bm25_docs.append((doc_id, content, metadata))

            # Build BM25 index
            bm25_count = self.bm25_indexer.index_documents(bm25_docs)

            logger.msg(
                "documents_indexed_hybrid",
                bm25_count=bm25_count,
                total_documents=len(documents)
            )

            return {
                "status": "success",
                "bm25_indexed": bm25_count,
                "total_documents": len(documents)
            }

        except Exception as e:
            logger.msg(
                "index_documents_error",
                error=str(e)
            )
            raise RetrievalError(f"Failed to index documents: {e}")

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_cache: bool = True,
        use_reranking: bool = True,
        fuse_top_k: int = 20
    ) -> Tuple[List[SearchResult], HybridSearchStats]:
        """Perform hybrid search.

        Pipeline:
        1. Check semantic cache
        2. BM25 sparse retrieval
        3. Dense (vector) retrieval
        4. RRF fusion
        5. Cross-encoder reranking
        6. Cache results

        Args:
            query: Query string
            top_k: Final number of results to return
            use_cache: Use semantic cache
            use_reranking: Use cross-encoder reranking
            fuse_top_k: Number of results to fuse before reranking

        Returns:
            Tuple of (results, stats)
        """
        start_time = time.time()
        cache_hit = False
        cache_similarity = None

        try:
            # 1. Get query embedding
            query_embedding = self.embedding_generator.embed_text(query)

            # 2. Check semantic cache
            if use_cache:
                cached_results = self.semantic_cache.get(query, query_embedding)
                if cached_results:
                    stats = HybridSearchStats(
                        query=query,
                        total_time_ms=(time.time() - start_time) * 1000,
                        cache_hit=True,
                        cache_similarity=1.0,
                        final_results=len(cached_results)
                    )
                    logger.msg("hybrid_search_cache_hit", query=query[:100])
                    return cached_results, stats

            # 3. Sparse retrieval (BM25)
            bm25_results = self.bm25_indexer.search(query, top_k=fuse_top_k)

            # 4. Dense retrieval (ChromaDB)
            dense_results = self._dense_search(query_embedding, top_k=fuse_top_k)

            # 5. RRF Fusion
            fused_results = self._fuse_results(
                bm25_results,
                dense_results,
                top_k=fuse_top_k
            )

            # 6. Cross-encoder reranking
            if use_reranking and len(fused_results) > 0:
                final_results = self.reranker.rerank(
                    query,
                    fused_results,
                    top_k=top_k
                )
            else:
                final_results = fused_results[:top_k]

            # 7. Cache results
            if use_cache and final_results:
                self.semantic_cache.set(query, query_embedding, final_results)

            # Build stats
            stats = HybridSearchStats(
                query=query,
                total_time_ms=(time.time() - start_time) * 1000,
                cache_hit=cache_hit,
                cache_similarity=cache_similarity,
                bm25_results=len(bm25_results),
                dense_results=len(dense_results),
                fused_results=len(fused_results),
                reranked_results=len(final_results) if use_reranking else 0,
                final_results=len(final_results)
            )

            logger.msg(
                "hybrid_search_complete",
                query_length=len(query),
                bm25_results=len(bm25_results),
                dense_results=len(dense_results),
                final_results=len(final_results),
                duration_ms=stats.total_time_ms
            )

            return final_results, stats

        except Exception as e:
            logger.msg(
                "hybrid_search_error",
                query=query[:100],
                error=str(e)
            )
            raise RetrievalError(f"Hybrid search failed: {e}")

    def _dense_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10
    ) -> List[SearchResult]:
        """Dense search using ChromaDB vector embeddings.

        Args:
            query_embedding: Pre-computed query embedding
            top_k: Number of results

        Returns:
            List of SearchResult objects
        """
        try:
            # Query ChromaDB
            results = self.vector_store.search(
                self.collection_name,
                [query_embedding.tolist()],
                n_results=top_k
            )

            # Parse results
            search_results = []
            if results and results.get("documents"):
                docs = results["documents"][0]
                distances = results.get("distances", [[]])[0] if results.get("distances") else []
                ids = results.get("ids", [[]])[0] if results.get("ids") else []
                metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

                for rank, (doc_id, content) in enumerate(zip(ids, docs)):
                    # Convert distance to similarity (1 - distance for L2 norm)
                    distance = distances[rank] if rank < len(distances) else 0
                    similarity = 1 - distance if distance else 0.5

                    metadata = metadatas[rank] if rank < len(metadatas) else {}

                    search_results.append(SearchResult(
                        doc_id=doc_id,
                        content=content,
                        score=max(0, similarity),
                        metadata=metadata,
                        source="dense",
                        retrieval_rank=rank
                    ))

            return search_results

        except Exception as e:
            logger.msg(
                "dense_search_error",
                collection=self.collection_name,
                error=str(e)
            )
            return []

    def _fuse_results(
        self,
        bm25_results: List[SearchResult],
        dense_results: List[SearchResult],
        top_k: int = 20
    ) -> List[SearchResult]:
        """Fuse BM25 and dense results using Reciprocal Rank Fusion (RRF).

        RRF formula: score = 1 / (k + rank) where k=60 (default)

        Weighted combination with alpha (default 0.5 = equal weight):
        final_score = alpha * rrf_bm25 + (1 - alpha) * rrf_dense

        Args:
            bm25_results: BM25 search results
            dense_results: Dense search results
            top_k: Number of results to return

        Returns:
            Fused and ranked results
        """
        # Create doc_id -> result mapping
        doc_results = {}

        # Add BM25 results with RRF scores
        for rank, result in enumerate(bm25_results):
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            if result.doc_id not in doc_results:
                doc_results[result.doc_id] = {
                    "result": result,
                    "bm25_rrf": rrf_score,
                    "dense_rrf": 0.0
                }
            else:
                doc_results[result.doc_id]["bm25_rrf"] = rrf_score

        # Add dense results with RRF scores
        for rank, result in enumerate(dense_results):
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            if result.doc_id not in doc_results:
                doc_results[result.doc_id] = {
                    "result": result,
                    "bm25_rrf": 0.0,
                    "dense_rrf": rrf_score
                }
            else:
                doc_results[result.doc_id]["dense_rrf"] = rrf_score

        # Compute fused scores
        fused = []
        for doc_id, scores in doc_results.items():
            bm25_rrf = scores["bm25_rrf"]
            dense_rrf = scores["dense_rrf"]
            fused_score = self.rrf_alpha * bm25_rrf + (1 - self.rrf_alpha) * dense_rrf

            result = scores["result"]
            result.score = fused_score
            result.source = "fused"
            fused.append(result)

        # Sort by fused score and return top-k
        fused.sort(key=lambda x: x.score, reverse=True)

        for rank, result in enumerate(fused[:top_k]):
            result.retrieval_rank = rank

        logger.msg(
            "rrf_fusion_complete",
            bm25_docs=len(bm25_results),
            dense_docs=len(dense_results),
            fused_docs=len(fused),
            top_k=top_k,
            rrf_alpha=self.rrf_alpha
        )

        return fused[:top_k]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get semantic cache statistics."""
        return self.semantic_cache.stats()

    def clear_cache(self) -> None:
        """Clear semantic query cache."""
        self.semantic_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get overall hybrid search statistics."""
        return {
            "semantic_cache": self.semantic_cache.stats(),
            "rrf_config": {
                "k": self.rrf_k,
                "alpha": self.rrf_alpha
            }
        }
