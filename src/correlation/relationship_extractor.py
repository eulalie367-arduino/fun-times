"""Extract relationships from text.

Identifies and classifies relationships between entities.
"""

from typing import List, Dict, Tuple, Optional
import logging
import re

logger = logging.getLogger(__name__)


class RelationshipType:
    """Define relationship types."""

    PERSON_KNOWS = "knows"
    PERSON_WORKS_FOR = "works_for"
    PERSON_MARRIED_TO = "married_to"
    ORG_OWNS = "owns"
    ORG_LOCATED_IN = "located_in"
    ENTITY_RELATED_TO = "related_to"
    DOCUMENT_MENTIONS = "mentions"


class Relationship:
    """Container for relationship."""

    def __init__(
        self,
        entity1: str,
        entity2: str,
        rel_type: str,
        confidence: float = 0.8
    ):
        """Initialize relationship.

        Args:
            entity1: First entity
            entity2: Second entity
            rel_type: Relationship type
            confidence: Confidence score
        """
        self.entity1 = entity1
        self.entity2 = entity2
        self.rel_type = rel_type
        self.confidence = confidence

    def __repr__(self):
        return f"{self.entity1} --{self.rel_type}--> {self.entity2} ({self.confidence:.2f})"


class RelationshipExtractor:
    """Extract relationships from text."""

    def __init__(self):
        """Initialize extractor."""
        self.relationship_patterns = {
            'works_for': r'(\w+) works? for (\w+)',
            'married_to': r'(\w+) (?:is )?married to (\w+)',
            'located_in': r'(\w+) (?:is )?located in (\w+)',
            'owns': r'(\w+) owns (\w+)',
            'related_to': r'(\w+) (?:is )?related to (\w+)',
            'mentions': r'(\w+) mentions? (\w+)'
        }
        self.relationships: List[Relationship] = []

    def extract_relationships(self, text: str) -> List[Relationship]:
        """Extract relationships from text.

        Args:
            text: Input text

        Returns:
            List of extracted relationships
        """
        relationships = []

        for rel_type, pattern in self.relationship_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity1, entity2 = match.groups()

                rel = Relationship(
                    entity1=entity1,
                    entity2=entity2,
                    rel_type=rel_type,
                    confidence=0.85
                )

                relationships.append(rel)
                self.relationships.append(rel)

        logger.debug(f"Extracted {len(relationships)} relationships from text")

        return relationships

    def get_relationships_for_entity(self, entity: str) -> List[Relationship]:
        """Get relationships for an entity.

        Args:
            entity: Entity name

        Returns:
            List of relationships involving entity
        """
        return [
            rel for rel in self.relationships
            if rel.entity1.lower() == entity.lower()
            or rel.entity2.lower() == entity.lower()
        ]

    def get_relationships_of_type(self, rel_type: str) -> List[Relationship]:
        """Get relationships of a specific type.

        Args:
            rel_type: Relationship type

        Returns:
            List of relationships of that type
        """
        return [
            rel for rel in self.relationships
            if rel.rel_type == rel_type
        ]

    def get_relationship_pairs(self) -> Dict[Tuple[str, str], List[str]]:
        """Get relationship pairs and their types.

        Returns:
            Dictionary of (entity1, entity2) -> list of relationship types
        """
        pairs = {}

        for rel in self.relationships:
            key = tuple(sorted([rel.entity1, rel.entity2]))

            if key not in pairs:
                pairs[key] = []

            if rel.rel_type not in pairs[key]:
                pairs[key].append(rel.rel_type)

        return pairs

    def get_stats(self) -> Dict[str, int]:
        """Get extraction statistics.

        Returns:
            Dictionary with metrics
        """
        return {
            'total_relationships': len(self.relationships),
            'unique_pairs': len(self.get_relationship_pairs()),
            'relationship_types': len(
                set(rel.rel_type for rel in self.relationships)
            )
        }
