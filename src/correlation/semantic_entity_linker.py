"""Semantic entity linking with transformer embeddings."""

from typing import List, Dict, Tuple, Optional
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EntityEmbedding:
    """Entity with semantic embedding."""
    entity_id: str
    entity_name: str
    entity_type: str
    embedding: np.ndarray
    aliases: List[str] = None


class SemanticEntityLinker:
    """Link entities using semantic similarity via transformer embeddings."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize semantic entity linker.

        Args:
            model_name: HuggingFace model name for embeddings
        """
        self.model_name = model_name
        self.model = None
        self.entity_embeddings: Dict[str, EntityEmbedding] = {}
        self.embedding_dim = None
        self._load_model()

    def _load_model(self) -> None:
        """Load sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded semantic model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not available, using random embeddings")
            self.embedding_dim = 384

    def add_entity(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        aliases: Optional[List[str]] = None
    ) -> None:
        """Add entity to knowledge base.

        Args:
            entity_id: Unique entity ID
            entity_name: Entity name
            entity_type: Entity type
            aliases: Alternative names
        """
        if self.model:
            embedding = self.model.encode(entity_name)
        else:
            embedding = np.random.randn(self.embedding_dim)

        self.entity_embeddings[entity_id] = EntityEmbedding(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            embedding=embedding,
            aliases=aliases or [entity_name]
        )

        logger.debug(f"Added entity: {entity_name}")

    def link_entity(
        self,
        mention_text: str,
        context: Optional[str] = None,
        threshold: float = 0.7
    ) -> Optional[Tuple[str, float]]:
        """Link mention to best matching entity.

        Args:
            mention_text: Mention text to link
            context: Surrounding context for disambiguation
            threshold: Minimum similarity threshold

        Returns:
            (entity_id, confidence) or None
        """
        if not self.entity_embeddings:
            return None

        # Encode mention with context
        if context:
            query_text = f"{context} {mention_text}"
        else:
            query_text = mention_text

        if self.model:
            query_embedding = self.model.encode(query_text)
        else:
            query_embedding = np.random.randn(self.embedding_dim)

        # Find best matching entity
        best_entity_id = None
        best_similarity = -1.0

        for entity_id, entity in self.entity_embeddings.items():
            # Check alias matches first (exact/fuzzy)
            for alias in entity.aliases:
                if mention_text.lower() in alias.lower() or alias.lower() in mention_text.lower():
                    return (entity_id, 0.95)  # High confidence for alias match

            # Compute semantic similarity
            similarity = self._cosine_similarity(query_embedding, entity.embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_entity_id = entity_id

        if best_similarity >= threshold and best_entity_id:
            return (best_entity_id, best_similarity)

        return None

    def resolve_coreference(
        self,
        mentions: List[str],
        context: Optional[str] = None
    ) -> List[Tuple[int, int, float]]:
        """Resolve coreferences between mentions.

        Args:
            mentions: List of mentions
            context: Surrounding context

        Returns:
            List of (mention_i, mention_j, similarity) tuples
        """
        if self.model:
            embeddings = self.model.encode(mentions)
        else:
            embeddings = np.random.randn(len(mentions), self.embedding_dim)

        coreferences = []

        for i in range(len(mentions)):
            for j in range(i + 1, len(mentions)):
                similarity = self._cosine_similarity(embeddings[i], embeddings[j])

                if similarity > 0.7:  # Coreference threshold
                    coreferences.append((i, j, similarity))

        return coreferences

    def cross_lingual_link(
        self,
        mention_text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[Tuple[str, float]]:
        """Link entity across languages.

        Args:
            mention_text: Mention in source language
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            (entity_id, confidence) or None
        """
        # In full implementation, would use multilingual model
        # For now, use existing English-based linking
        return self.link_entity(mention_text)

    def disambiguate_entity(
        self,
        mention_text: str,
        candidates: List[str],
        context: Optional[str] = None
    ) -> str:
        """Disambiguate between candidate entities.

        Args:
            mention_text: Mention text
            candidates: List of candidate entity IDs
            context: Surrounding context

        Returns:
            Best matching entity ID
        """
        if not candidates:
            return candidates[0] if candidates else None

        if context:
            query_text = f"{context} {mention_text}"
        else:
            query_text = mention_text

        if self.model:
            query_embedding = self.model.encode(query_text)
        else:
            query_embedding = np.random.randn(self.embedding_dim)

        best_entity_id = candidates[0]
        best_similarity = -1.0

        for entity_id in candidates:
            if entity_id not in self.entity_embeddings:
                continue

            entity = self.entity_embeddings[entity_id]
            similarity = self._cosine_similarity(query_embedding, entity.embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_entity_id = entity_id

        return best_entity_id

    def get_entity_neighbors(
        self,
        entity_id: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Get semantically similar entities.

        Args:
            entity_id: Query entity ID
            top_k: Number of neighbors to return

        Returns:
            List of (entity_id, similarity) tuples
        """
        if entity_id not in self.entity_embeddings:
            return []

        query_embedding = self.entity_embeddings[entity_id].embedding
        similarities = []

        for other_id, other_entity in self.entity_embeddings.items():
            if other_id == entity_id:
                continue

            similarity = self._cosine_similarity(query_embedding, other_entity.embedding)
            similarities.append((other_id, similarity))

        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def get_statistics(self) -> Dict:
        """Get linker statistics."""
        return {
            'total_entities': len(self.entity_embeddings),
            'embedding_dimension': self.embedding_dim,
            'model': self.model_name,
            'has_model': self.model is not None
        }
