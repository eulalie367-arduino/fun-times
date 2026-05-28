"""Named Entity Recognition (NER) for entity extraction.

Identifies and classifies named entities in text.
"""

from typing import List, Dict, Tuple, Set
import logging
import re

logger = logging.getLogger(__name__)


class Entity:
    """Represents an entity."""

    def __init__(self, text: str, entity_type: str, start: int, end: int):
        """Initialize entity.

        Args:
            text: Entity text
            entity_type: Type of entity (PERSON, ORG, LOCATION, etc.)
            start: Start position in text
            end: End position in text
        """
        self.text = text
        self.entity_type = entity_type
        self.start = start
        self.end = end
        self.confidence = 1.0

    def __repr__(self):
        return f"Entity({self.text}, {self.entity_type}, {self.confidence:.2f})"


class NERModel:
    """Named Entity Recognition model."""

    def __init__(self):
        """Initialize NER model."""
        self.entity_patterns = {
            'PERSON': r'\b[A-Z][a-z]+ (?:[A-Z][a-z]+ ){0,2}[A-Z][a-z]+\b',
            'ORG': r'\b(?:Inc|Corp|Ltd|LLC|Company|Corporation|Group)\b',
            'LOCATION': r'\b(?:New York|Los Angeles|San Francisco|London|Paris|Tokyo)\b',
            'DATE': r'\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b',
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'URL': r'https?://[^\s]+'
        }
        self.entities_found: Dict[str, Set[str]] = {
            entity_type: set() for entity_type in self.entity_patterns
        }

    def extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text.

        Args:
            text: Input text

        Returns:
            List of extracted entities
        """
        entities = []

        for entity_type, pattern in self.entity_patterns.items():
            for match in re.finditer(pattern, text):
                entity = Entity(
                    text=match.group(),
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end()
                )
                entities.append(entity)
                self.entities_found[entity_type].add(match.group())

        # Sort by position
        entities.sort(key=lambda e: e.start)

        logger.debug(f"Extracted {len(entities)} entities from text")

        return entities

    def extract_entities_with_confidence(self, text: str) -> List[Entity]:
        """Extract entities with confidence scores.

        Args:
            text: Input text

        Returns:
            List of entities with confidence scores
        """
        entities = self.extract_entities(text)

        # Assign confidence based on entity type and pattern quality
        for entity in entities:
            if entity.entity_type in ('EMAIL', 'URL'):
                entity.confidence = 0.95
            elif entity.entity_type == 'DATE':
                entity.confidence = 0.90
            else:
                entity.confidence = 0.80

        return entities

    def get_unique_entities(self) -> Dict[str, Set[str]]:
        """Get all unique entities found.

        Returns:
            Dictionary of entity_type -> set of entity texts
        """
        return {
            entity_type: entities.copy()
            for entity_type, entities in self.entities_found.items()
            if entities
        }

    def get_stats(self) -> Dict[str, int]:
        """Get NER statistics.

        Returns:
            Dictionary with entity counts
        """
        return {
            entity_type: len(entities)
            for entity_type, entities in self.entities_found.items()
        }
