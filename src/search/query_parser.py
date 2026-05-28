"""Parse and expand complex search queries.

Handles boolean operators, field-specific search, and query expansion.
"""

from typing import List, Dict, Set, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuery:
    """Represents a parsed query."""
    keywords: List[str]
    phrases: List[str]
    field_queries: Dict[str, str]  # field_name -> query
    must_include: Set[str]
    must_exclude: Set[str]
    original: str


class QueryParser:
    """Parse complex search queries."""

    def __init__(self):
        """Initialize query parser."""
        self.operators = {'+', '-', '"', ':', 'AND', 'OR', 'NOT'}

    def parse(self, query: str) -> ParsedQuery:
        """Parse query string.

        Args:
            query: Query string with operators

        Returns:
            Parsed query object
        """
        query = query.strip()
        keywords = []
        phrases = []
        field_queries = {}
        must_include = set()
        must_exclude = set()

        tokens = self._tokenize(query)

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Handle phrases
            if token.startswith('"') and token.endswith('"'):
                phrase = token[1:-1]
                phrases.append(phrase)
                i += 1

            # Handle must-include (+)
            elif token.startswith('+'):
                term = token[1:]
                must_include.add(term)
                keywords.append(term)
                i += 1

            # Handle must-exclude (-)
            elif token.startswith('-'):
                term = token[1:]
                must_exclude.add(term)
                i += 1

            # Handle field-specific search
            elif ':' in token:
                field, value = token.split(':', 1)
                field_queries[field] = value
                i += 1

            # Skip boolean operators
            elif token.upper() in {'AND', 'OR', 'NOT'}:
                i += 1

            # Regular keyword
            else:
                keywords.append(token)
                i += 1

        return ParsedQuery(
            keywords=keywords,
            phrases=phrases,
            field_queries=field_queries,
            must_include=must_include,
            must_exclude=must_exclude,
            original=query
        )

    def _tokenize(self, query: str) -> List[str]:
        """Tokenize query string.

        Args:
            query: Query string

        Returns:
            List of tokens
        """
        tokens = []
        current = ""
        in_quotes = False

        for char in query:
            if char == '"':
                in_quotes = not in_quotes
                current += char
            elif char == ' ' and not in_quotes:
                if current:
                    tokens.append(current)
                current = ""
            else:
                current += char

        if current:
            tokens.append(current)

        return tokens

    def expand_query(self, query: ParsedQuery, synonyms: Dict[str, List[str]]) -> ParsedQuery:
        """Expand query with synonyms.

        Args:
            query: Parsed query
            synonyms: Dictionary of term -> synonyms

        Returns:
            Expanded query
        """
        expanded_keywords = []

        for keyword in query.keywords:
            expanded_keywords.append(keyword)

            if keyword in synonyms:
                expanded_keywords.extend(synonyms[keyword])

        expanded = ParsedQuery(
            keywords=expanded_keywords,
            phrases=query.phrases,
            field_queries=query.field_queries,
            must_include=query.must_include,
            must_exclude=query.must_exclude,
            original=query.original
        )

        logger.debug(
            f"Query expanded from {len(query.keywords)} to {len(expanded_keywords)} terms"
        )

        return expanded

    def suggest_corrections(self, query: str, dictionary: Set[str]) -> List[str]:
        """Suggest query corrections.

        Args:
            query: Original query
            dictionary: Set of valid terms

        Returns:
            List of suggested corrected queries
        """
        suggestions = []
        tokens = self._tokenize(query)

        for i, token in enumerate(tokens):
            if token not in dictionary:
                # Find similar terms
                corrections = self._find_similar(token, dictionary, max_distance=1)

                for correction in corrections:
                    corrected = tokens.copy()
                    corrected[i] = correction
                    suggestions.append(" ".join(corrected))

        return suggestions[:5]  # Return top 5

    def _find_similar(
        self,
        term: str,
        dictionary: Set[str],
        max_distance: int = 1
    ) -> List[str]:
        """Find similar terms in dictionary.

        Args:
            term: Term to find similar to
            dictionary: Set of valid terms
            max_distance: Maximum edit distance

        Returns:
            List of similar terms
        """
        similar = []

        for dict_term in dictionary:
            if self._edit_distance(term, dict_term) <= max_distance:
                similar.append(dict_term)

        return sorted(similar, key=lambda x: self._edit_distance(term, x))

    @staticmethod
    def _edit_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance
        """
        if len(s1) < len(s2):
            return QueryParser._edit_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]
