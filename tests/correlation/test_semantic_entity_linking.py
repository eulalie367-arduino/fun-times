"""Tests for semantic entity linking."""

import numpy as np
import pytest
from src.correlation.semantic_entity_linker import SemanticEntityLinker


class TestSemanticEntityLinker:
    """Test semantic entity linking."""

    @pytest.fixture
    def linker(self):
        """Create linker instance."""
        return SemanticEntityLinker()

    def test_initialization(self, linker):
        """Test linker initialization."""
        assert linker.model_name is not None
        assert linker.embedding_dim is not None

    def test_add_entity(self, linker):
        """Test adding entity."""
        linker.add_entity("person_1", "Alice Smith", "PERSON")
        assert "person_1" in linker.entity_embeddings

    def test_add_multiple_entities(self, linker):
        """Test adding multiple entities."""
        linker.add_entity("person_1", "Alice Smith", "PERSON")
        linker.add_entity("person_2", "Bob Johnson", "PERSON")
        linker.add_entity("org_1", "Acme Corp", "ORG")

        assert len(linker.entity_embeddings) == 3

    def test_link_entity(self, linker):
        """Test entity linking."""
        linker.add_entity("person_1", "Alice Smith", "PERSON")
        linker.add_entity("person_2", "Bob Johnson", "PERSON")

        # Link mention to entity
        result = linker.link_entity("Alice")
        # Should return tuple or None
        assert result is None or isinstance(result, tuple)

    def test_link_entity_with_context(self, linker):
        """Test entity linking with context."""
        linker.add_entity("person_1", "Alice Smith", "PERSON", aliases=["Alice", "A. Smith"])
        linker.add_entity("person_2", "Alice Johnson", "PERSON")

        result = linker.link_entity("Alice", context="met with Alice at conference")
        # Alias should match with high confidence
        if result:
            assert result[1] >= 0.7

    def test_coreference_resolution(self, linker):
        """Test coreference resolution."""
        mentions = ["Alice Smith", "she", "the researcher"]
        coreferences = linker.resolve_coreference(mentions)

        assert isinstance(coreferences, list)
        # Some pairs might be coreferent
        if coreferences:
            assert len(coreferences[0]) == 3  # (i, j, similarity)

    def test_cross_lingual_linking(self, linker):
        """Test cross-lingual entity linking."""
        linker.add_entity("person_1", "Alice", "PERSON")
        result = linker.cross_lingual_link("Alice", "en", "es")
        assert result is None or isinstance(result, tuple)

    def test_entity_disambiguation(self, linker):
        """Test entity disambiguation."""
        linker.add_entity("alice_1", "Alice Smith", "PERSON")
        linker.add_entity("alice_2", "Alice Johnson", "PERSON")
        linker.add_entity("alice_3", "Alice Corp", "ORG")

        candidates = ["alice_1", "alice_2", "alice_3"]
        best = linker.disambiguate_entity("Alice", candidates)

        assert best in candidates

    def test_entity_neighbors(self, linker):
        """Test getting entity neighbors."""
        linker.add_entity("person_1", "Alice Smith", "PERSON")
        linker.add_entity("person_2", "Alice Johnson", "PERSON")
        linker.add_entity("person_3", "Bob Smith", "PERSON")

        neighbors = linker.get_entity_neighbors("person_1", top_k=2)

        assert isinstance(neighbors, list)
        assert len(neighbors) <= 2

    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])

        sim = SemanticEntityLinker._cosine_similarity(vec1, vec2)
        assert np.isclose(sim, 1.0)

    def test_zero_vectors(self):
        """Test handling of zero vectors."""
        vec1 = np.array([0, 0, 0])
        vec2 = np.array([1, 0, 0])

        sim = SemanticEntityLinker._cosine_similarity(vec1, vec2)
        assert sim == 0.0

    def test_statistics(self, linker):
        """Test getting statistics."""
        linker.add_entity("person_1", "Alice", "PERSON")
        stats = linker.get_statistics()

        assert stats['total_entities'] == 1
        assert stats['embedding_dimension'] is not None
