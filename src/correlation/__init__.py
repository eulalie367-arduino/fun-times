"""Phase 4C: CORRELATION detection modules.

Entity extraction, linking, relationship detection, knowledge graphs, and correlation engines.
"""

from .ner_model import NERModel, Entity
from .entity_linker import EntityLinker
from .relationship_extractor import RelationshipExtractor, Relationship, RelationshipType
from .knowledge_graph import KnowledgeGraph
from .correlation_engine import CorrelationEngine, CorrelationType, CorrelationScore
from .timeline_builder import TimelineBuilder, TimelineEvent

__all__ = [
    'NERModel',
    'Entity',
    'EntityLinker',
    'RelationshipExtractor',
    'Relationship',
    'RelationshipType',
    'KnowledgeGraph',
    'CorrelationEngine',
    'CorrelationType',
    'CorrelationScore',
    'TimelineBuilder',
    'TimelineEvent',
]
