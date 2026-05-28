"""Neo4j backend for knowledge graph persistence and querying."""

from typing import List, Dict, Optional, Set, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    max_pool_size: int = 50
    connection_timeout: int = 30


class Neo4jGraphBackend:
    """Neo4j-based knowledge graph backend."""

    def __init__(self, config: Neo4jConfig):
        """Initialize Neo4j backend.

        Args:
            config: Neo4j configuration
        """
        self.config = config
        self.driver = None
        self._init_driver()

    def _init_driver(self) -> None:
        """Initialize Neo4j driver."""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
                max_pool_size=self.config.max_pool_size,
                connection_timeout=self.config.connection_timeout
            )
            logger.info(f"Connected to Neo4j: {self.config.uri}")
        except ImportError:
            logger.warning("neo4j package not installed, using in-memory fallback")
            self.driver = None

    def add_entity(self, entity_id: str, entity_type: str, properties: Dict) -> bool:
        """Add entity to knowledge graph.

        Args:
            entity_id: Entity identifier
            entity_type: Entity type (PERSON, ORG, etc.)
            properties: Entity properties

        Returns:
            Success status
        """
        if not self.driver:
            return False

        try:
            with self.driver.session(database=self.config.database) as session:
                query = f"""
                CREATE (e:{entity_type} {{id: $id, name: $name}})
                SET e += $props
                RETURN e
                """
                session.run(query, id=entity_id, name=properties.get('name'), props=properties)
                return True
        except Exception as e:
            logger.error(f"Error adding entity: {e}")
            return False

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict] = None
    ) -> bool:
        """Add relationship between entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            rel_type: Relationship type
            properties: Relationship properties

        Returns:
            Success status
        """
        if not self.driver:
            return False

        try:
            with self.driver.session(database=self.config.database) as session:
                query = f"""
                MATCH (s {{id: $source}}), (t {{id: $target}})
                CREATE (s)-[r:{rel_type}]->(t)
                SET r += $props
                RETURN r
                """
                session.run(
                    query,
                    source=source_id,
                    target=target_id,
                    props=properties or {}
                )
                return True
        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            return False

    def find_shortest_path(self, source_id: str, target_id: str, max_depth: int = 5) -> Optional[List]:
        """Find shortest path between entities using BFS via Cypher.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_depth: Maximum path depth

        Returns:
            Path as list of entity IDs
        """
        if not self.driver:
            return None

        try:
            with self.driver.session(database=self.config.database) as session:
                query = f"""
                MATCH path = shortestPath(
                    (s {{id: $source}})-[*..{max_depth}]-(t {{id: $target}})
                )
                RETURN [node IN nodes(path) | node.id] AS path
                """
                result = session.run(query, source=source_id, target=target_id)
                record = result.single()
                return record['path'] if record else None
        except Exception as e:
            logger.error(f"Error finding path: {e}")
            return None

    def get_neighbors(self, entity_id: str, depth: int = 1) -> List[str]:
        """Get neighboring entities.

        Args:
            entity_id: Entity ID
            depth: Relationship depth

        Returns:
            List of neighbor entity IDs
        """
        if not self.driver:
            return []

        try:
            with self.driver.session(database=self.config.database) as session:
                query = f"""
                MATCH (e {{id: $id}})-[*1..{depth}]-(n)
                RETURN DISTINCT n.id AS neighbor
                """
                result = session.run(query, id=entity_id)
                return [record['neighbor'] for record in result]
        except Exception as e:
            logger.error(f"Error getting neighbors: {e}")
            return []

    def find_communities(self, entity_id: str, depth: int = 2) -> Set[str]:
        """Find entity communities using graph traversal.

        Args:
            entity_id: Entity ID
            depth: Traversal depth

        Returns:
            Set of community entity IDs
        """
        if not self.driver:
            return set()

        try:
            with self.driver.session(database=self.config.database) as session:
                query = f"""
                MATCH (e {{id: $id}})-[*1..{depth}]-(c)
                RETURN COLLECT(DISTINCT c.id) AS community
                """
                result = session.run(query, id=entity_id)
                record = result.single()
                return set(record['community']) if record else set()
        except Exception as e:
            logger.error(f"Error finding communities: {e}")
            return set()

    def get_entity_statistics(self) -> Dict:
        """Get knowledge graph statistics.

        Returns:
            Statistics dictionary
        """
        if not self.driver:
            return {}

        try:
            with self.driver.session(database=self.config.database) as session:
                # Entity count
                entity_result = session.run("MATCH (n) RETURN count(n) AS count")
                entity_count = entity_result.single()['count']

                # Relationship count
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
                rel_count = rel_result.single()['count']

                # Entity types
                type_result = session.run("MATCH (n) RETURN DISTINCT labels(n) AS types")
                entity_types = set()
                for record in type_result:
                    entity_types.update(record['types'])

                return {
                    'total_entities': entity_count,
                    'total_relationships': rel_count,
                    'entity_types': list(entity_types)
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")


class Neo4jIndexOptimizer:
    """Optimize Neo4j indexes and queries."""

    def __init__(self, backend: Neo4jGraphBackend):
        """Initialize optimizer.

        Args:
            backend: Neo4j backend instance
        """
        self.backend = backend

    def create_indexes(self) -> bool:
        """Create optimal indexes for queries."""
        if not self.backend.driver:
            return False

        try:
            with self.backend.driver.session() as session:
                # Entity ID index
                session.run("CREATE INDEX entity_id_index IF NOT EXISTS FOR (n) ON (n.id)")
                # Entity type index
                session.run("CREATE INDEX entity_type_index IF NOT EXISTS FOR (n:Entity) ON (n.type)")
                # Relationship type index
                session.run("CREATE INDEX rel_type_index IF NOT EXISTS FOR ()-[r]-() ON (r.type)")
                logger.info("Created Neo4j indexes")
                return True
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False

    def analyze_query_performance(self, query: str) -> Dict:
        """Analyze query performance with EXPLAIN.

        Args:
            query: Cypher query

        Returns:
            Query plan analysis
        """
        if not self.backend.driver:
            return {}

        try:
            with self.backend.driver.session() as session:
                result = session.run(f"EXPLAIN {query}")
                plan = result.plan
                return {
                    'operator_count': len(plan.operations),
                    'estimated_rows': plan.args.get('EstimatedRows', 0),
                    'db_hits': plan.args.get('DbHits', 0)
                }
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return {}
