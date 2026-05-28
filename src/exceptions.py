"""Custom exceptions for RAG pipeline."""


class RAGException(Exception):
    """Base exception for RAG pipeline."""
    pass


class ConfigurationError(RAGException):
    """Raised when configuration is invalid or missing."""
    pass


class EmbeddingError(RAGException):
    """Raised when embedding generation fails."""
    pass


class VectorStoreError(RAGException):
    """Raised when vector store operations fail."""
    pass


class RetrievalError(RAGException):
    """Raised when retrieval operations fail."""
    pass


class PromptBuildError(RAGException):
    """Raised when prompt building fails."""
    pass


class LLMError(RAGException):
    """Raised when LLM API calls fail."""
    pass


class RateLimitError(RAGException):
    """Raised when rate limit is exceeded."""
    pass


class InputValidationError(RAGException):
    """Raised when input validation fails."""
    pass


class DatabaseError(RAGException):
    """Raised when database operations fail."""
    pass


class TimeoutError(RAGException):
    """Raised when operation times out."""
    pass


class AuthenticationError(RAGException):
    """Raised when authentication fails."""
    pass


class DataQualityError(RAGException):
    """Raised when data quality checks fail."""
    pass
