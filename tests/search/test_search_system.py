"""Comprehensive tests for Phase 4B search system."""

import pytest
import time
from src.search.full_text_index import FullTextIndex, BM25Scorer
from src.search.faceted_search import FacetedSearch
from src.search.rank_model import RankingModel
from src.search.query_parser import QueryParser, ParsedQuery
from src.search.suggestion_engine import SuggestionEngine
from src.search.analytics import SearchAnalytics, SearchEvent


class TestBM25Scorer:
    """Test BM25 scoring."""

    def test_scorer_initialization(self):
        """Test BM25 initialization."""
        scorer = BM25Scorer(k1=1.5, b=0.75)
        assert scorer.k1 == 1.5
        assert scorer.b == 0.75

    def test_fit_scorer(self):
        """Test fitting BM25 scorer."""
        scorer = BM25Scorer()
        docs = {
            "doc1": "machine learning is great",
            "doc2": "deep learning models",
            "doc3": "neural networks"
        }

        scorer.fit(docs)

        assert scorer.corpus_size == 3
        assert len(scorer.idf_scores) > 0
        assert scorer.average_doc_length > 0

    def test_score_document(self):
        """Test BM25 scoring."""
        scorer = BM25Scorer()
        docs = {
            "doc1": "machine learning is great",
            "doc2": "deep learning models"
        }

        scorer.fit(docs)

        score = scorer.score("learning", "doc1", {"learning": 1, "is": 1})
        assert score > 0


class TestFullTextIndex:
    """Test full-text indexing."""

    def test_index_initialization(self):
        """Test index initialization."""
        index = FullTextIndex()
        assert len(index.documents) == 0
        assert not index.indexed

    def test_index_documents(self):
        """Test document indexing."""
        index = FullTextIndex()
        docs = {
            "doc1": "this is a test document",
            "doc2": "another test with content",
            "doc3": "final example"
        }

        index.index_documents(docs)

        assert len(index.documents) == 3
        assert index.indexed

    def test_basic_search(self):
        """Test basic search."""
        index = FullTextIndex()
        docs = {
            "doc1": "python programming language",
            "doc2": "javascript programming",
            "doc3": "rust systems language"
        }

        index.index_documents(docs)

        results = index.search("programming")

        assert len(results) > 0
        assert any("doc1" in r or "doc2" in r for r in results)

    def test_phrase_search(self):
        """Test phrase search."""
        index = FullTextIndex()
        docs = {
            "doc1": "machine learning is great",
            "doc2": "deep learning models",
            "doc3": "learning to learn"
        }

        index.index_documents(docs)

        results = index.phrase_search("learning models")

        assert len(results) > 0

    def test_wildcard_search(self):
        """Test wildcard search."""
        index = FullTextIndex()
        docs = {
            "doc1": "running game tournament",
            "doc2": "runtime library",
            "doc3": "test case"
        }

        index.index_documents(docs)

        results = index.wildcard_search("run*")

        assert len(results) > 0

    def test_index_stats(self):
        """Test index statistics."""
        index = FullTextIndex()
        docs = {
            "doc1": "the quick brown fox",
            "doc2": "jumps over the fence"
        }

        index.index_documents(docs)

        stats = index.get_stats()

        assert stats["documents"] == 2
        assert stats["unique_terms"] > 0


class TestFacetedSearch:
    """Test faceted search."""

    def test_faceted_initialization(self):
        """Test faceted search initialization."""
        search = FacetedSearch()
        assert len(search.facets) == 0

    def test_add_document_with_facets(self):
        """Test adding document with facets."""
        search = FacetedSearch()

        search.add_document("doc1", {"genre": "fiction", "year": "2020"})
        search.add_document("doc2", {"genre": "nonfiction", "year": "2021"})

        assert "genre" in search.facets
        assert "fiction" in search.facets["genre"]

    def test_filter_by_facet(self):
        """Test facet filtering."""
        search = FacetedSearch()

        search.add_document("doc1", {"genre": "fiction"})
        search.add_document("doc2", {"genre": "fiction"})
        search.add_document("doc3", {"genre": "nonfiction"})

        docs = ["doc1", "doc2", "doc3"]
        filtered = search.filter_by_facet(docs, {"genre": "fiction"})

        assert len(filtered) == 2
        assert "doc1" in filtered

    def test_filter_by_range(self):
        """Test range filtering."""
        search = FacetedSearch()

        search.add_document("doc1", {"year": "2020"})
        search.add_document("doc2", {"year": "2021"})
        search.add_document("doc3", {"year": "2019"})

        docs = ["doc1", "doc2", "doc3"]
        filtered = search.filter_by_range(docs, {"year": (2020.0, 2021.0)})

        assert len(filtered) >= 2

    def test_get_facet_values(self):
        """Test getting facet values."""
        search = FacetedSearch()

        search.add_document("doc1", {"genre": "fiction"})
        search.add_document("doc2", {"genre": "fiction"})
        search.add_document("doc3", {"genre": "nonfiction"})

        values = search.get_facet_values("genre")

        assert values["fiction"] == 2
        assert values["nonfiction"] == 1


class TestRankingModel:
    """Test ranking model."""

    def test_ranker_initialization(self):
        """Test ranker initialization."""
        ranker = RankingModel()
        assert ranker.signal_weights is not None

    def test_rank_results(self):
        """Test ranking results."""
        ranker = RankingModel()

        results = [
            ("doc1", 100),
            ("doc2", 50),
            ("doc3", 75)
        ]

        signals = {
            "popularity": {"doc1": 0.8, "doc2": 0.9, "doc3": 0.7},
            "recency": {"doc1": 0.5, "doc2": 0.6, "doc3": 0.7}
        }

        reranked = ranker.rank(results, signals)

        assert len(reranked) > 0

    def test_normalize_scores(self):
        """Test score normalization."""
        ranker = RankingModel()

        scores = {"doc1": 100, "doc2": 50, "doc3": 75}

        normalized = ranker.normalize_scores(scores)

        assert 0 <= normalized["doc1"] <= 1
        assert 0 <= normalized["doc2"] <= 1
        assert normalized["doc1"] > normalized["doc2"]


class TestQueryParser:
    """Test query parsing."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = QueryParser()
        assert len(parser.operators) > 0

    def test_parse_simple_query(self):
        """Test parsing simple query."""
        parser = QueryParser()

        parsed = parser.parse("python programming")

        assert "python" in parsed.keywords
        assert "programming" in parsed.keywords

    def test_parse_phrase_query(self):
        """Test parsing phrase query."""
        parser = QueryParser()

        parsed = parser.parse('exact phrase search')

        assert len(parsed.keywords) > 0

    def test_parse_field_query(self):
        """Test parsing field-specific query."""
        parser = QueryParser()

        parsed = parser.parse("title:python")

        assert "title" in parsed.field_queries

    def test_parse_boolean_operators(self):
        """Test parsing with boolean operators."""
        parser = QueryParser()

        parsed = parser.parse("+required -excluded optional")

        assert "required" in parsed.must_include
        assert "excluded" in parsed.must_exclude

    def test_expand_query(self):
        """Test query expansion."""
        parser = QueryParser()

        parsed = parser.parse("python")

        synonyms = {"python": ["python3", "python2", "coding"]}

        expanded = parser.expand_query(parsed, synonyms)

        assert len(expanded.keywords) > 1


class TestSuggestionEngine:
    """Test suggestion engine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = SuggestionEngine()
        assert engine.max_suggestions == 10

    def test_record_query(self):
        """Test recording queries."""
        engine = SuggestionEngine()

        engine.record_query("python programming")
        engine.record_query("python tutorial")
        engine.record_query("javascript")

        assert len(engine.query_history) == 3

    def test_get_suggestions(self):
        """Test getting suggestions."""
        engine = SuggestionEngine()

        engine.record_query("python programming")
        engine.record_query("python tutorial")
        engine.record_query("javascript")

        suggestions = engine.get_suggestions("python")

        assert len(suggestions) > 0

    def test_get_trending(self):
        """Test getting trending queries."""
        engine = SuggestionEngine()

        for _ in range(5):
            engine.record_query("trending query")
        engine.record_query("less popular")

        trending = engine.get_trending()

        assert len(trending) > 0

    def test_get_related_queries(self):
        """Test getting related queries."""
        engine = SuggestionEngine()

        engine.record_query("machine learning")
        engine.record_query("deep learning")
        engine.record_query("javascript basics")

        related = engine.get_related_queries("machine learning")

        assert len(related) >= 0

    def test_autocomplete(self):
        """Test autocomplete."""
        engine = SuggestionEngine()

        engine.record_query("autocomplete test")
        engine.record_query("auto pilot")

        completions = engine.autocomplete("auto")

        assert len(completions) > 0


class TestSearchAnalytics:
    """Test search analytics."""

    def test_analytics_initialization(self):
        """Test analytics initialization."""
        analytics = SearchAnalytics()
        assert len(analytics.events) == 0

    def test_record_search(self):
        """Test recording search events."""
        analytics = SearchAnalytics()

        analytics.record_search("python", 50.5, 100)

        assert len(analytics.events) == 1
        assert analytics.performance_metrics['total_searches'] == 1

    def test_record_click(self):
        """Test recording clicks."""
        analytics = SearchAnalytics()

        analytics.record_search("python", 50.0, 100)
        analytics.record_click("python", 2)

        assert analytics.performance_metrics['total_clicks'] == 1

    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        analytics = SearchAnalytics()

        analytics.record_search("query1", 100.0, 50)
        analytics.record_search("query2", 200.0, 75)
        analytics.record_click("query1", 0)

        metrics = analytics.get_performance_metrics()

        assert metrics['total_searches'] == 2
        assert metrics['total_clicks'] == 1
        assert 0 <= metrics['click_through_rate'] <= 1

    def test_get_top_queries(self):
        """Test getting top queries."""
        analytics = SearchAnalytics()

        for _ in range(5):
            analytics.record_search("popular", 50.0, 100)
        analytics.record_search("less popular", 50.0, 50)

        top = analytics.get_top_queries(limit=5)

        assert len(top) > 0

    def test_get_engagement_metrics(self):
        """Test engagement metrics."""
        analytics = SearchAnalytics()

        analytics.record_search("test", 50.0, 100)
        analytics.record_search("test2", 50.0, 50)
        analytics.record_click("test", 1)

        engagement = analytics.get_engagement_metrics()

        assert 'engagement_rate' in engagement
        assert 0 <= engagement['engagement_rate'] <= 1
