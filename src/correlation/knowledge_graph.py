"""Knowledge graph for entity relationships.

Stores and queries entity relationships and connections.
"""

from typing import List, Dict, Set, Tuple, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class Relationship:
    """Represents a relationship between entities."""

    def __init__(self, source: str, target: str, rel_type: str, weight: float = 1.0):
        """Initialize relationship.

        Args:
            source: Source entity
            target: Target entity
            rel_type: Relationship type
            weight: Relationship strength (0-1)
        """
        self.source = source
        self.target = target
        self.rel_type = rel_type
        self.weight = weight

    def __repr__(self):
        return f"{self.source} --{self.rel_type}--> {self.target} ({self.weight:.2f})"


class KnowledgeGraph:
    """Store and query entity relationships."""

    def __init__(self):
        """Initialize knowledge graph."""
        self.relationships: List[Relationship] = []
        self.adjacency: Dict[str, List[Relationship]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[Relationship]] = defaultdict(list)
        self.entities: Set[str] = set()

    def add_entity(self, entity: str):
        """Add entity to graph.

        Args:
            entity: Entity name
        """
        self.entities.add(entity)

    def add_relationship(
        self,
        source: str,
        target: str,
        rel_type: str,
        weight: float = 1.0
    ):
        """Add relationship between entities.

        Args:
            source: Source entity
            target: Target entity
            rel_type: Relationship type
            weight: Relationship weight
        """
        rel = Relationship(source, target, rel_type, weight)
        self.relationships.append(rel)
        self.adjacency[source].append(rel)
        self.reverse_adjacency[target].append(rel)
        self.entities.add(source)
        self.entities.add(target)

        logger.debug(f"Added relationship: {rel}")

    def get_neighbors(self, entity: str) -> List[Tuple[str, str, float]]:
        """Get connected entities.

        Args:
            entity: Entity name

        Returns:
            List of (target_entity, relationship_type, weight) tuples
        """
        neighbors = []

        for rel in self.adjacency.get(entity, []):
            neighbors.append((rel.target, rel.rel_type, rel.weight))

        return neighbors

    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between entities.

        Args:
            source: Source entity
            target: Target entity

        Returns:
            Path as list of entities, or None if no path
        """
        if source == target:
            return [source]

        # BFS for shortest path
        queue = [(source, [source])]
        visited = {source}

        while queue:
            current, path = queue.pop(0)

            for neighbor, _, _ in self.get_neighbors(current):
                if neighbor == target:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_community(self, entity: str, depth: int = 2) -> Set[str]:
        """Find entities in same community.

        Args:
            entity: Starting entity
            depth: Search depth

        Returns:
            Set of connected entities within depth
        """
        community = {entity}
        current_level = {entity}

        for _ in range(depth):
            next_level = set()

            for current in current_level:
                for neighbor, _, _ in self.get_neighbors(current):
                    if neighbor not in community:
                        next_level.add(neighbor)
                        community.add(neighbor)

            current_level = next_level

        return community

    def get_stats(self) -> Dict[str, int]:
        """Get graph statistics.

        Returns:
            Dictionary with graph metrics
        """
        return {
            'entities': len(self.entities),
            'relationships': len(self.relationships),
            'density': len(self.relationships) / (len(self.entities) ** 2)
            if self.entities else 0
        }
