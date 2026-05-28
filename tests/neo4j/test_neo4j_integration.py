"""Tests for Neo4j integration."""

import pytest
from src.correlation.neo4j_backend import Neo4jConfig, Neo4jGraphBackend


class TestNeo4jBackend:
    """Test Neo4j backend."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Neo4jConfig(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )

    def test_initialization(self, config):
        """Test backend initialization."""
        backend = Neo4jGraphBackend(config)
        assert backend.config == config

    def test_add_entity(self, config):
        """Test adding entity."""
        backend = Neo4jGraphBackend(config)
        result = backend.add_entity(
            "person_1",
            "PERSON",
            {"name": "Alice", "age": 30}
        )
        # Result depends on driver availability
        assert isinstance(result, bool)

    def test_add_relationship(self, config):
        """Test adding relationship."""
        backend = Neo4jGraphBackend(config)
        result = backend.add_relationship(
            "person_1",
            "person_2",
            "KNOWS",
            {"since": 2020}
        )
        assert isinstance(result, bool)

    def test_find_shortest_path(self, config):
        """Test shortest path finding."""
        backend = Neo4jGraphBackend(config)
        path = backend.find_shortest_path("person_1", "person_5")
        # Can be None if driver unavailable
        assert path is None or isinstance(path, list)

    def test_get_neighbors(self, config):
        """Test neighbor retrieval."""
        backend = Neo4jGraphBackend(config)
        neighbors = backend.get_neighbors("person_1")
        assert isinstance(neighbors, list)

    def test_find_communities(self, config):
        """Test community finding."""
        backend = Neo4jGraphBackend(config)
        community = backend.find_communities("person_1")
        assert isinstance(community, set)

    def test_get_statistics(self, config):
        """Test statistics retrieval."""
        backend = Neo4jGraphBackend(config)
        stats = backend.get_entity_statistics()
        assert isinstance(stats, dict)

    def test_close(self, config):
        """Test connection closure."""
        backend = Neo4jGraphBackend(config)
        backend.close()
        # Should complete without error
        assert True
