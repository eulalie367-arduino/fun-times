"""Entity linking to knowledge base.

Links extracted entities to a knowledge base.
"""

from typing import Dict, List, Optional, Tuple
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EntityLinker:
    """Link entities to knowledge base."""

    def __init__(self):
        """Initialize entity linker."""
        self.knowledge_base: Dict[str, Dict[str, str]] = {}
        self.aliases: Dict[str, str] = {}  # alias -> canonical form
        self.entity_types: Dict[str, str] = {}  # entity -> type

    def add_entity(
        self,
        entity_id: str,
        canonical_name: str,
        entity_type: str,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None
    ):
        """Add entity to knowledge base.

        Args:
            entity_id: Unique entity ID
            canonical_name: Canonical entity name
            entity_type: Entity type
            aliases: Alternative names
            metadata: Additional metadata
        """
        self.knowledge_base[entity_id] = {
            'name': canonical_name,
            'type': entity_type,
            'metadata': metadata or {}
        }

        self.entity_types[canonical_name] = entity_type
        self.aliases[canonical_name.lower()] = entity_id

        # Add aliases
        for alias in (aliases or []):
            self.aliases[alias.lower()] = entity_id
            self.entity_types[alias] = entity_type

        logger.debug(f"Added entity: {canonical_name}")

    def link_entity(self, entity_text: str) -> Optional[Tuple[str, str]]:
        """Link entity text to knowledge base.

        Args:
            entity_text: Entity text to link

        Returns:
            Tuple of (entity_id, canonical_name) or None
        """
        entity_lower = entity_text.lower()

        # Exact match
        if entity_lower in self.aliases:
            entity_id = self.aliases[entity_lower]
            canonical = self.knowledge_base[entity_id]['name']
            return (entity_id, canonical)

        # Partial match
        for alias, entity_id in self.aliases.items():
            if alias in entity_lower or entity_lower in alias:
                canonical = self.knowledge_base[entity_id]['name']
                return (entity_id, canonical)

        return None

    def get_entity_info(self, entity_id: str) -> Optional[Dict[str, str]]:
        """Get information for entity.

        Args:
            entity_id: Entity ID

        Returns:
            Entity information or None
        """
        return self.knowledge_base.get(entity_id)

    def get_related_entities(self, entity_id: str) -> List[Tuple[str, str]]:
        """Get entities of same type.

        Args:
            entity_id: Entity ID

        Returns:
            List of (entity_id, canonical_name) tuples
        """
        if entity_id not in self.knowledge_base:
            return []

        entity_type = self.knowledge_base[entity_id]['type']

        related = []
        for ent_id, info in self.knowledge_base.items():
            if info['type'] == entity_type and ent_id != entity_id:
                related.append((ent_id, info['name']))

        return related

    def get_stats(self) -> Dict[str, int]:
        """Get linker statistics.

        Returns:
            Dictionary with metrics
        """
        type_counts = defaultdict(int)

        for info in self.knowledge_base.values():
            type_counts[info['type']] += 1

        return {
            'entities': len(self.knowledge_base),
            'aliases': len(self.aliases),
            'types': dict(type_counts)
        }
