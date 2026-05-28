"""Correlation detection engine for finding relationships.

Detects various types of correlations between entities and documents.
"""

from typing import List, Dict, Tuple, Set
import logging
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


class CorrelationType:
    """Define correlation types."""

    SEMANTIC_SIMILARITY = "semantic_similarity"
    CO_OCCURRENCE = "co_occurrence"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    ENTITY = "entity_relationship"
    DOCUMENT = "document_similarity"
    TREND = "trend_correlation"


class CorrelationScore:
    """Container for correlation score and metadata."""

    def __init__(
        self,
        score: float,
        correlation_type: str,
        confidence: float = 0.8
    ):
        """Initialize correlation score.

        Args:
            score: Score value (0-1)
            correlation_type: Type of correlation
            confidence: Confidence level (0-1)
        """
        self.score = score
        self.correlation_type = correlation_type
        self.confidence = confidence


class CorrelationEngine:
    """Detect correlations between entities."""

    def __init__(self):
        """Initialize correlation engine."""
        self.entity_frequencies: Dict[str, int] = defaultdict(int)
        self.document_entities: Dict[str, Set[str]] = {}
        self.entity_pairs: Dict[Tuple[str, str], int] = defaultdict(int)
        self.correlations: Dict[str, List[CorrelationScore]] = defaultdict(list)

    def record_document(self, doc_id: str, entities: List[str]):
        """Record entities in document.

        Args:
            doc_id: Document ID
            entities: List of entities in document
        """
        self.document_entities[doc_id] = set(entities)

        for entity in entities:
            self.entity_frequencies[entity] += 1

        # Record co-occurrences
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i + 1:]:
                key = tuple(sorted([entity1, entity2]))
                self.entity_pairs[key] += 1

    def detect_co_occurrence_correlation(self, min_frequency: int = 2) -> Dict[Tuple[str, str], float]:
        """Detect co-occurrence correlations.

        Args:
            min_frequency: Minimum co-occurrence count

        Returns:
            Dictionary of entity pairs -> correlation scores
        """
        correlations = {}

        for (entity1, entity2), count in self.entity_pairs.items():
            if count >= min_frequency:
                # PMI-like score
                freq1 = self.entity_frequencies[entity1]
                freq2 = self.entity_frequencies[entity2]
                total_docs = len(self.document_entities)

                pmi = math.log(count / (freq1 * freq2 / total_docs)) if (freq1 * freq2) > 0 else 0

                # Normalize to [0, 1]
                score = 1.0 / (1.0 + math.exp(-pmi))
                correlations[(entity1, entity2)] = score

        logger.info(f"Found {len(correlations)} co-occurrence correlations")

        return correlations

    def detect_temporal_correlation(
        self,
        events: List[Tuple[str, float]]  # (entity, timestamp)
    ) -> List[Tuple[str, str, float]]:
        """Detect temporal correlations.

        Args:
            events: List of (entity, timestamp) tuples

        Returns:
            List of (entity1, entity2, correlation) tuples
        """
        correlations = []

        # Group by time windows
        time_window = 3600  # 1 hour
        windowed_events = defaultdict(list)

        for entity, timestamp in events:
            window = int(timestamp // time_window)
            windowed_events[window].append(entity)

        # Find entities that appear in same time window
        for window, entities in windowed_events.items():
            unique_entities = set(entities)

            if len(unique_entities) > 1:
                for i, e1 in enumerate(sorted(unique_entities)):
                    for e2 in sorted(unique_entities)[i + 1:]:
                        freq1 = entities.count(e1)
                        freq2 = entities.count(e2)
                        score = (freq1 * freq2) / (len(entities) ** 2)
                        correlations.append((e1, e2, score))

        logger.info(f"Found {len(correlations)} temporal correlations")

        return correlations

    def detect_document_similarity(self, entity_threshold: float = 0.5) -> Dict[Tuple[str, str], float]:
        """Detect document similarity based on shared entities.

        Args:
            entity_threshold: Jaccard similarity threshold

        Returns:
            Dictionary of (doc1, doc2) -> similarity score
        """
        similarities = {}
        doc_ids = list(self.document_entities.keys())

        for i, doc1 in enumerate(doc_ids):
            for doc2 in doc_ids[i + 1:]:
                entities1 = self.document_entities[doc1]
                entities2 = self.document_entities[doc2]

                # Jaccard similarity
                intersection = len(entities1 & entities2)
                union = len(entities1 | entities2)

                if union > 0:
                    similarity = intersection / union

                    if similarity >= entity_threshold:
                        similarities[(doc1, doc2)] = similarity

        logger.info(f"Found {len(similarities)} similar document pairs")

        return similarities

    def get_entity_correlations(self, entity: str) -> List[Tuple[str, float, str]]:
        """Get all correlations for an entity.

        Args:
            entity: Entity name

        Returns:
            List of (correlated_entity, score, correlation_type) tuples
        """
        results = []

        # Co-occurrence correlations
        for (e1, e2), score in self.detect_co_occurrence_correlation().items():
            if e1 == entity:
                results.append((e2, score, CorrelationType.CO_OCCURRENCE))
            elif e2 == entity:
                results.append((e1, score, CorrelationType.CO_OCCURRENCE))

        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def get_stats(self) -> Dict[str, int]:
        """Get correlation engine statistics.

        Returns:
            Dictionary with metrics
        """
        return {
            'unique_entities': len(self.entity_frequencies),
            'documents_processed': len(self.document_entities),
            'entity_pairs': len(self.entity_pairs)
        }
