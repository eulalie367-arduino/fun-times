"""Phase 4B: SEARCHABLE system modules.

Full-text search, faceted search, ranking, query parsing, suggestions, and analytics.
"""

from .full_text_index import FullTextIndex, BM25Scorer
from .faceted_search import FacetedSearch
from .rank_model import RankingModel
from .query_parser import QueryParser, ParsedQuery
from .suggestion_engine import SuggestionEngine
from .analytics import SearchAnalytics, SearchEvent

__all__ = [
    'FullTextIndex',
    'BM25Scorer',
    'FacetedSearch',
    'RankingModel',
    'QueryParser',
    'ParsedQuery',
    'SuggestionEngine',
    'SearchAnalytics',
    'SearchEvent',
]
