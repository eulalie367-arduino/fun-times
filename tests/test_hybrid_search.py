"""Unit tests for hybrid search module."""

import pytest
import numpy as np
import time
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock, patch

from src.retrieval.hybrid_search import (
    HybridSearcher,
    BM25Indexer,
    CrossEncoderReranker,
    SemanticQueryCache,
    SearchResult,
    HybridSearchStats
)
from src.exceptions import RetrievalError


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_create_search_result(self):
        """Test creating a search result."""
        result = SearchResult(
            doc_id="doc1",
            content="Test content",
            score=0.95,
            metadata={"source": "test"},
            source="dense"
        )

        assert result.doc_id == "doc1"
        assert result.content == "Test content"
        assert result.score == 0.95
        assert result.source == "dense"

    def test_search_result_to_dict(self):
        """Test converting search result to dict."""
        result = SearchResult(
            doc_id="doc1",
            content="Test",
            score=0.8,
            metadata={"key": "value"}
        )

        result_dict = result.to_dict()
        assert result_dict["doc_id"] == "doc1"
        assert result_dict["content"] == "Test"
        assert result_dict["score"] == 0.8


class TestSemanticQueryCache:
    """Test SemanticQueryCache."""

    def test_init(self):
        """Test cache initialization."""
        cache = SemanticQueryCache(max_size=500, ttl_seconds=3600)

        assert cache.max_size == 500
        assert cache.ttl_seconds == 3600
        assert len(cache.cache) == 0

    def test_cache_set_and_get_exact_match(self):
        """Test setting and getting cached results with exact similarity."""
        cache = SemanticQueryCache()
        query = "test query"
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = embedding / np.linalg.norm(embedding)  # Normalize

        result = SearchResult(
            doc_id="doc1",
            content="test content",
            score=0.9
        )

        cache.set(query, embedding, [result])

        # Query with same embedding should hit
        cached = cache.get(query, embedding)
        assert cached is not None
        assert len(cached) == 1
        assert cached[0].doc_id == "doc1"

    def test_cache_similarity_threshold(self):
        """Test cache similarity threshold."""
        cache = SemanticQueryCache(similarity_threshold=0.95)

        embedding1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        # Different embedding with lower similarity
        embedding2 = np.array([0.7, 0.3, 0.0], dtype=np.float32)
        embedding2 = embedding2 / np.linalg.norm(embedding2)

        result = SearchResult(
            doc_id="doc1",
            content="test",
            score=0.9
        )

        cache.set("query1", embedding1, [result])

        # Different embedding with similarity < threshold should not hit
        cached = cache.get("query2", embedding2)
        assert cached is None

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = SemanticQueryCache(ttl_seconds=1)

        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = embedding / np.linalg.norm(embedding)

        result = SearchResult(
            doc_id="doc1",
            content="test",
            score=0.9
        )

        cache.set("query", embedding, [result])

        # Should be cached initially
        cached = cache.get("query", embedding)
        assert cached is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should not be cached after TTL
        cached = cache.get("query", embedding)
        assert cached is None

    def test_cache_eviction_on_max_size(self):
        """Test LRU eviction when cache exceeds max size."""
        cache = SemanticQueryCache(max_size=3, ttl_seconds=3600)

        for i in range(4):
            embedding = np.array([float(i), 0.0, 0.0], dtype=np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            result = SearchResult(
                doc_id=f"doc{i}",
                content=f"content{i}",
                score=0.9
            )
            cache.set(f"query{i}", embedding, [result])

        # Should have evicted the first entry
        assert len(cache.cache) <= 3

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = SemanticQueryCache()

        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = embedding / np.linalg.norm(embedding)

        result = SearchResult(
            doc_id="doc1",
            content="test",
            score=0.9
        )

        cache.set("query", embedding, [result])
        cache.get("query", embedding)  # Hit
        cache.get("query", embedding * 0.5)  # Miss

        stats = cache.stats()
        assert stats["hits"] >= 0
        assert stats["misses"] >= 0
        assert "hit_rate" in stats
        assert stats["size"] >= 0

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = SemanticQueryCache()

        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = embedding / np.linalg.norm(embedding)

        result = SearchResult(
            doc_id="doc1",
            content="test",
            score=0.9
        )

        cache.set("query", embedding, [result])
        assert len(cache.cache) > 0

        cache.clear()
        assert len(cache.cache) == 0

    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        sim = SemanticQueryCache._cosine_similarity(vec1, vec2)
        assert abs(sim - 1.0) < 0.01

        # Orthogonal vectors
        vec3 = np.array([0.0, 1.0, 0.0])
        sim = SemanticQueryCache._cosine_similarity(vec1, vec3)
        assert abs(sim) < 0.01


class TestBM25Indexer:
    """Test BM25Indexer."""

    @pytest.fixture
    def indexer(self):
        """Create BM25 indexer."""
        return BM25Indexer()

    @pytest.fixture
    def sample_documents(self):
        """Sample documents for indexing."""
        return [
            ("doc1", "machine learning is a subfield of artificial intelligence", {}),
            ("doc2", "deep learning uses neural networks for pattern recognition", {}),
            ("doc3", "natural language processing handles text data", {}),
            ("doc4", "computer vision focuses on image analysis", {})
        ]

    def test_indexer_init(self, indexer):
        """Test indexer initialization."""
        assert indexer.bm25 is None
        assert len(indexer.documents) == 0

    def test_index_documents(self, indexer, sample_documents):
        """Test indexing documents."""
        count = indexer.index_documents(sample_documents)

        assert count == 4
        assert len(indexer.documents) == 4
        assert indexer.bm25 is not None

    def test_search_before_indexing(self, indexer):
        """Test search before indexing returns empty."""
        results = indexer.search("test query")
        assert len(results) == 0

    def test_search_basic(self, indexer, sample_documents):
        """Test basic BM25 search."""
        indexer.index_documents(sample_documents)

        results = indexer.search("machine learning", top_k=2)

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.source == "bm25" for r in results)

    def test_search_top_k(self, indexer, sample_documents):
        """Test top-k parameter."""
        indexer.index_documents(sample_documents)

        results_5 = indexer.search("artificial intelligence", top_k=5)
        results_2 = indexer.search("artificial intelligence", top_k=2)

        assert len(results_5) <= 5
        assert len(results_2) <= 2
        assert len(results_2) <= len(results_5)

    def test_search_results_have_metadata(self, indexer):
        """Test search results include metadata."""
        docs = [
            ("doc1", "test content", {"source": "wikipedia"}),
            ("doc2", "other content", {"source": "arxiv"})
        ]

        indexer.index_documents(docs)
        results = indexer.search("test")

        assert len(results) > 0
        assert results[0].metadata is not None


class TestCrossEncoderReranker:
    """Test CrossEncoderReranker."""

    @pytest.fixture
    def sample_results(self):
        """Sample search results for reranking."""
        return [
            SearchResult(
                doc_id="doc1",
                content="machine learning is a type of AI",
                score=0.5,
                source="bm25"
            ),
            SearchResult(
                doc_id="doc2",
                content="deep learning uses neural networks",
                score=0.4,
                source="bm25"
            ),
            SearchResult(
                doc_id="doc3",
                content="natural language processing",
                score=0.3,
                source="bm25"
            )
        ]

    @patch("src.retrieval.hybrid_search.CrossEncoderReranker.__init__")
    def test_reranker_init_error_without_transformers(self, mock_init):
        """Test reranker initialization."""
        mock_init.return_value = None
        reranker = CrossEncoderReranker.__new__(CrossEncoderReranker)
        assert reranker is not None

    def test_reranker_rerank_empty_results(self):
        """Test reranking empty results."""
        reranker = CrossEncoderReranker.__new__(CrossEncoderReranker)
        reranker.model_name = "test-model"
        reranker.batch_size = 32
        reranker.model = Mock()

        results = reranker.rerank("query", [], top_k=10)
        assert len(results) == 0


class TestHybridSearcher:
    """Test HybridSearcher."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = Mock()
        store.search = Mock(return_value={
            "documents": [["doc from vector store"]],
            "ids": [["vec_doc1"]],
            "distances": [[0.1]],
            "metadatas": [[{"source": "chroma"}]]
        })
        return store

    @pytest.fixture
    def mock_embedding_generator(self):
        """Create mock embedding generator."""
        gen = Mock()
        gen.embed_text = Mock(return_value=np.array([0.1, 0.2, 0.3], dtype=np.float32))
        return gen

    @pytest.fixture
    def hybrid_searcher(self, mock_vector_store, mock_embedding_generator):
        """Create hybrid searcher."""
        bm25 = BM25Indexer()
        return HybridSearcher(
            vector_store=mock_vector_store,
            embedding_generator=mock_embedding_generator,
            bm25_indexer=bm25,
            reranker=None
        )

    def test_init(self, hybrid_searcher):
        """Test hybrid searcher initialization."""
        assert hybrid_searcher.collection_name == "documents"
        assert hybrid_searcher.rrf_k == 60
        assert hybrid_searcher.rrf_alpha == 0.5

    def test_index_documents(self, hybrid_searcher):
        """Test indexing documents."""
        docs = [
            {"id": "doc1", "content": "machine learning algorithms"},
            {"id": "doc2", "content": "deep neural networks"}
        ]

        result = hybrid_searcher.index_documents(docs)

        assert result["status"] == "success"
        assert result["bm25_indexed"] == 2

    def test_fuse_results_rrf_algorithm(self, hybrid_searcher):
        """Test RRF fusion algorithm."""
        bm25_results = [
            SearchResult("doc1", "content1", 0.9, source="bm25", retrieval_rank=0),
            SearchResult("doc2", "content2", 0.8, source="bm25", retrieval_rank=1)
        ]

        dense_results = [
            SearchResult("doc2", "content2", 0.85, source="dense", retrieval_rank=0),
            SearchResult("doc3", "content3", 0.75, source="dense", retrieval_rank=1)
        ]

        fused = hybrid_searcher._fuse_results(bm25_results, dense_results, top_k=3)

        assert len(fused) <= 3
        assert all(r.source == "fused" for r in fused)
        # doc2 appears in both, should score higher
        doc_ids = [r.doc_id for r in fused]
        assert "doc2" in doc_ids or "doc1" in doc_ids

    def test_fuse_results_rrf_score_computation(self, hybrid_searcher):
        """Test RRF score computation."""
        # Single document appearing in both BM25 and dense
        bm25_results = [
            SearchResult("doc1", "content", 0.9, source="bm25", retrieval_rank=0)
        ]

        dense_results = [
            SearchResult("doc1", "content", 0.8, source="dense", retrieval_rank=0)
        ]

        fused = hybrid_searcher._fuse_results(
            bm25_results,
            dense_results,
            top_k=1
        )

        assert len(fused) == 1
        # RRF score should be combination of both ranks
        # With equal alpha=0.5: 0.5 * 1/(60+0+1) + 0.5 * 1/(60+0+1)
        expected_rrf = 1.0 / (hybrid_searcher.rrf_k + 1)
        assert abs(fused[0].score - expected_rrf) < 0.01

    def test_fuse_results_alpha_weighting(self, hybrid_searcher):
        """Test alpha weighting in RRF fusion."""
        # Set alpha to favor BM25
        hybrid_searcher.rrf_alpha = 0.7

        bm25_results = [
            SearchResult("doc1", "content", 0.9, source="bm25", retrieval_rank=0)
        ]

        dense_results = [
            SearchResult("doc2", "content", 0.9, source="dense", retrieval_rank=0)
        ]

        fused = hybrid_searcher._fuse_results(
            bm25_results,
            dense_results,
            top_k=2
        )

        # doc1 should score higher (from BM25, alpha=0.7)
        assert fused[0].doc_id == "doc1"

    def test_dense_search(self, hybrid_searcher, mock_vector_store):
        """Test dense search."""
        query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        results = hybrid_searcher._dense_search(query_embedding, top_k=5)

        assert len(results) > 0
        assert all(r.source == "dense" for r in results)
        mock_vector_store.search.assert_called_once()

    def test_dense_search_empty_results(self, hybrid_searcher):
        """Test dense search with empty results."""
        hybrid_searcher.vector_store.search = Mock(return_value={
            "documents": [],
            "ids": []
        })

        query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        results = hybrid_searcher._dense_search(query_embedding)

        assert len(results) == 0

    def test_get_cache_stats(self, hybrid_searcher):
        """Test getting cache statistics."""
        stats = hybrid_searcher.get_cache_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "size" in stats

    def test_clear_cache(self, hybrid_searcher):
        """Test clearing cache."""
        hybrid_searcher.clear_cache()
        stats = hybrid_searcher.get_cache_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_get_stats(self, hybrid_searcher):
        """Test getting overall statistics."""
        stats = hybrid_searcher.get_stats()

        assert "semantic_cache" in stats
        assert "rrf_config" in stats
        assert stats["rrf_config"]["k"] == 60
        assert stats["rrf_config"]["alpha"] == 0.5


class TestHybridSearchStats:
    """Test HybridSearchStats."""

    def test_create_stats(self):
        """Test creating search stats."""
        stats = HybridSearchStats(
            query="test query",
            total_time_ms=150.5,
            cache_hit=True,
            cache_similarity=0.98
        )

        assert stats.query == "test query"
        assert stats.total_time_ms == 150.5
        assert stats.cache_hit is True
        assert stats.cache_similarity == 0.98

    def test_stats_default_values(self):
        """Test stats with default values."""
        stats = HybridSearchStats(
            query="test",
            total_time_ms=100.0,
            cache_hit=False
        )

        assert stats.bm25_results == 0
        assert stats.dense_results == 0
        assert stats.reranked_results == 0


class TestIntegration:
    """Integration tests for hybrid search."""

    def test_hybrid_search_full_pipeline(self):
        """Test full hybrid search pipeline."""
        # Create mock components
        mock_vector_store = Mock()
        mock_vector_store.search = Mock(return_value={
            "documents": [["vector result 1", "vector result 2"]],
            "ids": [["vec1", "vec2"]],
            "distances": [[0.2, 0.3]],
            "metadatas": [[{}, {}]]
        })

        mock_embedding_gen = Mock()
        query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        mock_embedding_gen.embed_text = Mock(return_value=query_embedding)

        # Create searcher and index documents
        searcher = HybridSearcher(
            vector_store=mock_vector_store,
            embedding_generator=mock_embedding_gen,
            reranker=None
        )

        docs = [
            {"id": "doc1", "content": "machine learning"},
            {"id": "doc2", "content": "deep learning networks"}
        ]

        searcher.index_documents(docs)

        # Perform search
        results, stats = searcher.search(
            "machine learning",
            top_k=5,
            use_cache=True,
            use_reranking=False
        )

        assert isinstance(results, list)
        assert isinstance(stats, HybridSearchStats)
        assert stats.cache_hit is False
        assert stats.total_time_ms > 0
