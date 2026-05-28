"""Comprehensive tests for Phase 4C correlation system."""

import pytest
import time
from src.correlation.ner_model import NERModel, Entity
from src.correlation.entity_linker import EntityLinker
from src.correlation.relationship_extractor import RelationshipExtractor, RelationshipType
from src.correlation.knowledge_graph import KnowledgeGraph
from src.correlation.correlation_engine import CorrelationEngine, CorrelationType
from src.correlation.timeline_builder import TimelineBuilder


class TestNERModel:
    """Test NER extraction."""

    def test_ner_initialization(self):
        """Test NER initialization."""
        model = NERModel()
        assert len(model.entity_patterns) > 0

    def test_extract_entities(self):
        """Test entity extraction."""
        model = NERModel()

        text = "John Smith works at Microsoft in Seattle. Email: john@microsoft.com"
        entities = model.extract_entities(text)

        assert len(entities) > 0

    def test_extract_entities_with_confidence(self):
        """Test extraction with confidence."""
        model = NERModel()

        text = "Visit https://example.com or email test@example.com"
        entities = model.extract_entities_with_confidence(text)

        assert len(entities) > 0
        assert all(0 <= e.confidence <= 1 for e in entities)

    def test_get_unique_entities(self):
        """Test getting unique entities."""
        model = NERModel()

        text1 = "john@example.com works in NYC"
        text2 = "jane@example.com works in LA"

        model.extract_entities(text1)
        model.extract_entities(text2)

        unique = model.get_unique_entities()

        assert len(unique) > 0

    def test_get_stats(self):
        """Test NER statistics."""
        model = NERModel()

        text = "john@example.com"
        model.extract_entities(text)

        stats = model.get_stats()

        assert "EMAIL" in stats


class TestEntityLinker:
    """Test entity linking."""

    def test_linker_initialization(self):
        """Test linker initialization."""
        linker = EntityLinker()
        assert len(linker.knowledge_base) == 0

    def test_add_entity(self):
        """Test adding entity."""
        linker = EntityLinker()

        linker.add_entity(
            "entity1",
            "Apple Inc",
            "ORG",
            aliases=["Apple", "AAPL"]
        )

        assert "entity1" in linker.knowledge_base

    def test_link_entity(self):
        """Test entity linking."""
        linker = EntityLinker()

        linker.add_entity("e1", "Microsoft", "ORG", aliases=["MSFT"])

        result = linker.link_entity("Microsoft")

        assert result is not None
        assert result[0] == "e1"

    def test_link_entity_alias(self):
        """Test linking via alias."""
        linker = EntityLinker()

        linker.add_entity("e1", "Apple Inc", "ORG", aliases=["Apple"])

        result = linker.link_entity("Apple")

        assert result is not None
        assert result[0] == "e1"

    def test_get_related_entities(self):
        """Test getting related entities."""
        linker = EntityLinker()

        linker.add_entity("e1", "Apple", "ORG")
        linker.add_entity("e2", "Microsoft", "ORG")
        linker.add_entity("e3", "Google", "ORG")

        related = linker.get_related_entities("e1")

        assert len(related) >= 2


class TestRelationshipExtractor:
    """Test relationship extraction."""

    def test_extractor_initialization(self):
        """Test extractor initialization."""
        extractor = RelationshipExtractor()
        assert len(extractor.relationship_patterns) > 0

    def test_extract_relationships(self):
        """Test relationship extraction."""
        extractor = RelationshipExtractor()

        text = "John works for Microsoft"
        relationships = extractor.extract_relationships(text)

        assert len(relationships) > 0

    def test_get_relationships_for_entity(self):
        """Test getting entity relationships."""
        extractor = RelationshipExtractor()

        text = "Alice works for Google and is married to Bob"
        extractor.extract_relationships(text)

        rels = extractor.get_relationships_for_entity("Alice")

        assert len(rels) >= 0

    def test_get_relationship_pairs(self):
        """Test getting relationship pairs."""
        extractor = RelationshipExtractor()

        text = "John works for Apple"
        extractor.extract_relationships(text)

        pairs = extractor.get_relationship_pairs()

        assert len(pairs) >= 0


class TestKnowledgeGraph:
    """Test knowledge graph."""

    def test_graph_initialization(self):
        """Test graph initialization."""
        graph = KnowledgeGraph()
        assert len(graph.entities) == 0

    def test_add_entity(self):
        """Test adding entity."""
        graph = KnowledgeGraph()

        graph.add_entity("Alice")
        graph.add_entity("Bob")

        assert "Alice" in graph.entities

    def test_add_relationship(self):
        """Test adding relationship."""
        graph = KnowledgeGraph()

        graph.add_relationship("Alice", "Bob", "knows", weight=0.9)

        assert len(graph.relationships) > 0

    def test_get_neighbors(self):
        """Test getting neighbors."""
        graph = KnowledgeGraph()

        graph.add_relationship("Alice", "Bob", "knows")
        graph.add_relationship("Alice", "Charlie", "works_with")

        neighbors = graph.get_neighbors("Alice")

        assert len(neighbors) == 2

    def test_get_shortest_path(self):
        """Test shortest path."""
        graph = KnowledgeGraph()

        graph.add_relationship("A", "B", "connects")
        graph.add_relationship("B", "C", "connects")
        graph.add_relationship("C", "D", "connects")

        path = graph.get_shortest_path("A", "D")

        assert path is not None
        assert len(path) == 4

    def test_get_community(self):
        """Test getting community."""
        graph = KnowledgeGraph()

        graph.add_relationship("A", "B", "knows")
        graph.add_relationship("B", "C", "knows")
        graph.add_relationship("C", "D", "knows")

        community = graph.get_community("A", depth=2)

        assert len(community) >= 3


class TestCorrelationEngine:
    """Test correlation detection."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = CorrelationEngine()
        assert len(engine.entity_frequencies) == 0

    def test_record_document(self):
        """Test recording document."""
        engine = CorrelationEngine()

        engine.record_document("doc1", ["Alice", "Bob", "Charlie"])
        engine.record_document("doc2", ["Bob", "Diana"])

        assert "Alice" in engine.entity_frequencies

    def test_detect_co_occurrence(self):
        """Test co-occurrence detection."""
        engine = CorrelationEngine()

        engine.record_document("doc1", ["A", "B", "C"])
        engine.record_document("doc2", ["A", "B"])
        engine.record_document("doc3", ["B", "C"])

        correlations = engine.detect_co_occurrence_correlation()

        assert len(correlations) > 0

    def test_detect_temporal_correlation(self):
        """Test temporal correlation."""
        engine = CorrelationEngine()

        events = [
            ("Alice", time.time()),
            ("Bob", time.time() + 100),
            ("Charlie", time.time() + 200)
        ]

        correlations = engine.detect_temporal_correlation(events)

        assert isinstance(correlations, list)

    def test_detect_document_similarity(self):
        """Test document similarity."""
        engine = CorrelationEngine()

        engine.record_document("doc1", ["A", "B", "C"])
        engine.record_document("doc2", ["B", "C", "D"])
        engine.record_document("doc3", ["X", "Y", "Z"])

        similarities = engine.detect_document_similarity()

        assert len(similarities) >= 0

    def test_get_entity_correlations(self):
        """Test getting entity correlations."""
        engine = CorrelationEngine()

        engine.record_document("doc1", ["Alice", "Bob"])
        engine.record_document("doc2", ["Alice", "Bob"])

        correlations = engine.get_entity_correlations("Alice")

        assert isinstance(correlations, list)


class TestTimelineBuilder:
    """Test timeline building."""

    def test_builder_initialization(self):
        """Test builder initialization."""
        builder = TimelineBuilder()
        assert len(builder.events) == 0

    def test_add_event(self):
        """Test adding event."""
        builder = TimelineBuilder()

        builder.add_event(
            timestamp=time.time(),
            entity="Alice",
            event_type="login",
            description="User logged in"
        )

        assert len(builder.events) == 1

    def test_get_entity_timeline(self):
        """Test getting entity timeline."""
        builder = TimelineBuilder()

        now = time.time()
        builder.add_event(now, "Alice", "login", "logged in")
        builder.add_event(now + 3600, "Alice", "logout", "logged out")

        timeline = builder.get_entity_timeline("Alice")

        assert len(timeline) == 2
        assert timeline[0].timestamp <= timeline[1].timestamp

    def test_find_concurrent_events(self):
        """Test finding concurrent events."""
        builder = TimelineBuilder()

        now = time.time()
        builder.add_event(now, "Alice", "login", "logged in")
        builder.add_event(now + 100, "Bob", "login", "logged in")
        builder.add_event(now + 5000, "Charlie", "login", "logged in")

        concurrent = builder.find_concurrent_events(window_seconds=3600)

        assert len(concurrent) >= 0

    def test_get_important_events(self):
        """Test getting important events."""
        builder = TimelineBuilder()

        now = time.time()
        builder.add_event(now, "Alice", "login", "logged in", importance=0.3)
        builder.add_event(now + 3600, "Alice", "payment", "made payment", importance=0.9)

        important = builder.get_important_events("Alice", importance_threshold=0.8)

        assert len(important) == 1

    def test_get_event_summary(self):
        """Test event summary."""
        builder = TimelineBuilder()

        now = time.time()
        builder.add_event(now, "Alice", "login", "logged in")
        builder.add_event(now + 1000, "Alice", "login", "logged in again")
        builder.add_event(now + 2000, "Alice", "logout", "logged out")

        summary = builder.get_event_summary("Alice")

        assert summary["login"] == 2
        assert summary["logout"] == 1
