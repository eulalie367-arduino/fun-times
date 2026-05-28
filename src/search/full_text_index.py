"""Full-text search index with BM25 and phrase search support.

Implements inverted index with BM25 scoring for efficient text retrieval.
"""

from typing import Dict, List, Set, Tuple, Optional
import logging
import math
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class BM25Scorer:
    """BM25 scoring algorithm for relevance ranking."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """Initialize BM25 scorer.

        Args:
            k1: Term frequency saturation parameter (default 1.5)
            b: Length normalization parameter (default 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.average_doc_length = 0.0
        self.doc_lengths: Dict[str, int] = {}
        self.idf_scores: Dict[str, float] = {}

    def fit(self, documents: Dict[str, str]):
        """Fit BM25 model on corpus.

        Args:
            documents: Dictionary of doc_id -> text
        """
        self.corpus_size = len(documents)
        self.doc_lengths = {
            doc_id: len(text.split())
            for doc_id, text in documents.items()
        }

        # Calculate average document length
        if self.doc_lengths:
            self.average_doc_length = sum(self.doc_lengths.values()) / len(
                self.doc_lengths
            )

        # Calculate IDF scores
        term_doc_count = defaultdict(int)

        for text in documents.values():
            for term in set(text.lower().split()):
                term_doc_count[term] += 1

        for term, count in term_doc_count.items():
            self.idf_scores[term] = math.log(
                1 + (self.corpus_size - count + 0.5) / (count + 0.5)
            )

        logger.info(
            f"BM25 fitted on {self.corpus_size} documents, "
            f"{len(self.idf_scores)} unique terms"
        )

    def score(self, query: str, doc_id: str, frequencies: Dict[str, int]) -> float:
        """Calculate BM25 score for a document.

        Args:
            query: Query string
            doc_id: Document ID
            frequencies: Term frequency map for document

        Returns:
            BM25 score
        """
        score = 0.0
        doc_len = self.doc_lengths.get(doc_id, 0)

        for term in query.lower().split():
            if term not in self.idf_scores:
                continue

            idf = self.idf_scores[term]
            freq = frequencies.get(term, 0)

            # BM25 formula
            numerator = freq * (self.k1 + 1)
            denominator = freq + self.k1 * (
                1 - self.b + self.b * (doc_len / self.average_doc_length)
            )

            score += idf * (numerator / denominator)

        return score


class FullTextIndex:
    """Full-text search index with BM25 scoring."""

    def __init__(self):
        """Initialize full-text index."""
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.term_frequencies: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self.documents: Dict[str, str] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.scorer = BM25Scorer()
        self.indexed = False

    def index_documents(self, documents: Dict[str, str]):
        """Index documents for full-text search.

        Args:
            documents: Dictionary of doc_id -> text
        """
        self.documents = documents.copy()

        for doc_id, text in documents.items():
            self._index_document(doc_id, text)

        # Fit BM25 scorer
        self.scorer.fit(documents)
        self.indexed = True

        logger.info(f"Indexed {len(documents)} documents")

    def _index_document(self, doc_id: str, text: str):
        """Index a single document.

        Args:
            doc_id: Document ID
            text: Document text
        """
        terms = text.lower().split()
        self.doc_lengths[doc_id] = len(terms)

        term_freq: Dict[str, int] = defaultdict(int)

        for term in terms:
            self.inverted_index[term].add(doc_id)
            term_freq[term] += 1

        self.term_frequencies[doc_id] = dict(term_freq)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Search for documents matching query.

        Args:
            query: Query string
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples
        """
        if not self.indexed:
            return []

        # Find candidate documents
        candidate_docs = set()
        for term in query.lower().split():
            candidate_docs.update(self.inverted_index.get(term, set()))

        # Score candidates
        results = []
        for doc_id in candidate_docs:
            score = self.scorer.score(
                query,
                doc_id,
                self.term_frequencies.get(doc_id, {})
            )
            results.append((doc_id, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def phrase_search(self, phrase: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Search for exact phrase.

        Args:
            phrase: Phrase to search for
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples
        """
        results = []
        phrase_lower = phrase.lower()

        for doc_id, text in self.documents.items():
            if phrase_lower in text.lower():
                score = 100.0 + text.lower().count(phrase_lower) * 10
                results.append((doc_id, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def wildcard_search(self, pattern: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Search with wildcard pattern.

        Args:
            pattern: Pattern with * wildcards (e.g., "act*")
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples
        """
        # Convert wildcard pattern to regex-like matching
        pattern_parts = pattern.split("*")

        results = []
        for term in self.inverted_index.keys():
            # Check if term matches pattern
            matches = True
            last_pos = 0

            for i, part in enumerate(pattern_parts):
                if part:
                    pos = term.find(part, last_pos)
                    if pos == -1:
                        matches = False
                        break
                    if i == 0 and pos != 0:  # First part must be at start
                        matches = False
                        break
                    last_pos = pos + len(part)

            if matches:
                for doc_id in self.inverted_index[term]:
                    results.append((doc_id, len(term)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_stats(self) -> Dict[str, int]:
        """Get index statistics.

        Returns:
            Dictionary with index metrics
        """
        return {
            "documents": len(self.documents),
            "unique_terms": len(self.inverted_index),
            "average_doc_length": (
                sum(self.doc_lengths.values()) / len(self.doc_lengths)
                if self.doc_lengths else 0
            )
        }
