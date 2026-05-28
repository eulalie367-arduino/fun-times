"""Faceted search with filtering and aggregation capabilities.

Enables filtering search results by multiple facets (categories, dates, etc.).
"""

from typing import Dict, List, Set, Tuple, Any, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class FacetedSearch:
    """Support faceted filtering on search results."""

    def __init__(self):
        """Initialize faceted search."""
        self.facets: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self.document_facets: Dict[str, Dict[str, str]] = {}

    def add_document(
        self,
        doc_id: str,
        facet_values: Dict[str, str]
    ):
        """Add document with facet values.

        Args:
            doc_id: Document ID
            facet_values: Dictionary of facet_name -> value
        """
        self.document_facets[doc_id] = facet_values.copy()

        for facet_name, value in facet_values.items():
            self.facets[facet_name][value].add(doc_id)

    def filter_by_facet(
        self,
        doc_ids: List[str],
        facet_filters: Dict[str, str]
    ) -> List[str]:
        """Filter documents by facet values.

        Args:
            doc_ids: List of document IDs to filter
            facet_filters: Dictionary of facet_name -> value filters

        Returns:
            Filtered document IDs
        """
        result = set(doc_ids)

        for facet_name, value in facet_filters.items():
            matching_docs = self.facets[facet_name].get(value, set())
            result = result.intersection(matching_docs)

        return list(result)

    def filter_by_range(
        self,
        doc_ids: List[str],
        range_filters: Dict[str, Tuple[float, float]]
    ) -> List[str]:
        """Filter documents by numeric ranges.

        Args:
            doc_ids: List of document IDs to filter
            range_filters: Dictionary of facet_name -> (min, max) tuples

        Returns:
            Filtered document IDs matching all ranges
        """
        result = []

        for doc_id in doc_ids:
            facets = self.document_facets.get(doc_id, {})
            matches_all = True

            for facet_name, (min_val, max_val) in range_filters.items():
                try:
                    value = float(facets.get(facet_name, 0))
                    if not (min_val <= value <= max_val):
                        matches_all = False
                        break
                except (ValueError, TypeError):
                    matches_all = False
                    break

            if matches_all:
                result.append(doc_id)

        return result

    def get_facet_values(self, facet_name: str) -> Dict[str, int]:
        """Get all values for a facet and their counts.

        Args:
            facet_name: Name of facet

        Returns:
            Dictionary of value -> count
        """
        if facet_name not in self.facets:
            return {}

        return {
            value: len(doc_ids)
            for value, doc_ids in self.facets[facet_name].items()
        }

    def get_facet_suggestions(
        self,
        current_filters: Dict[str, str]
    ) -> Dict[str, Dict[str, int]]:
        """Get available facet values given current filters.

        Args:
            current_filters: Current facet filters applied

        Returns:
            Dictionary of facet_name -> value counts
        """
        # Find documents matching current filters
        all_docs = set()
        for doc_id in self.document_facets.keys():
            all_docs.add(doc_id)

        for facet_name, value in current_filters.items():
            if facet_name in self.facets:
                all_docs = all_docs.intersection(
                    self.facets[facet_name].get(value, set())
                )

        # Get facets for matching documents
        suggestions = defaultdict(lambda: defaultdict(int))

        for doc_id in all_docs:
            facets = self.document_facets.get(doc_id, {})
            for facet_name, value in facets.items():
                suggestions[facet_name][value] += 1

        return {k: dict(v) for k, v in suggestions.items()}

    def get_stats(self) -> Dict[str, Any]:
        """Get facet statistics.

        Returns:
            Dictionary with facet metrics
        """
        return {
            "total_facets": len(self.facets),
            "total_values": sum(
                len(values) for values in self.facets.values()
            ),
            "total_documents": len(self.document_facets),
            "facets": {
                name: len(values)
                for name, values in self.facets.items()
            }
        }
