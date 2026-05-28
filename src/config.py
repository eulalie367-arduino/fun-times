"""Configuration management for RAG pipeline."""
import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment and config files."""

    # Project
    project_name: str = "RAG Pipeline"
    version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # API Keys
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")

    # Embedding
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    embedding_batch_size: int = 32
    cache_embeddings: bool = True

    # Chunking
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")
    chunk_min_length: int = 10
    chunk_max_length: int = 2000

    # Retrieval
    top_k: int = Field(default=5, env="TOP_K")
    similarity_threshold: float = 0.5
    reranking_enabled: bool = False
    deduplication_enabled: bool = True

    # Vector Store
    chromadb_host: str = Field(default="localhost", env="CHROMADB_HOST")
    chromadb_port: int = Field(default=8000, env="CHROMADB_PORT")
    chromadb_path: str = Field(default="/data/chroma", env="CHROMADB_PATH")
    chromadb_mode: str = Field(default="persistent", env="CHROMADB_MODE")

    # Cache
    cache_enabled: bool = True
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_backend: str = "memory"
    redis_url: str = "redis://localhost:6379"

    # Cache Tiers (Multi-tier caching for local-first RAG)
    cache_l1_max_size: int = Field(default=1000, env="CACHE_L1_MAX_SIZE")
    cache_l1_ttl: int = Field(default=3600, env="CACHE_L1_TTL")
    cache_l2_enabled: bool = Field(default=True, env="CACHE_L2_ENABLED")
    cache_l2_path: str = Field(default="/data/cache", env="CACHE_L2_PATH")
    cache_l2_max_size_mb: int = Field(default=500, env="CACHE_L2_MAX_SIZE_MB")

    # Embedding Configuration
    embedding_cache_enabled: bool = True
    embedding_cache_ttl: int = 7200
    embedding_batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    embedding_device: str = Field(default="auto", env="EMBEDDING_DEVICE")

    # Semantic Chunking
    semantic_chunking_enabled: bool = False
    semantic_similarity_threshold: float = 0.85
    chunk_semantic_window: int = 3

    # LLM
    llm_model: str = Field(default="claude-opus-4-6", env="LLM_MODEL")
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_timeout: int = 30

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: str = Field(default="/logs/rag.log", env="LOG_FILE")
    log_max_size_mb: int = 100
    log_backup_count: int = 5

    # Security
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")
    input_validation: bool = True
    sanitize_prompts: bool = True

    # Performance
    batch_processing: bool = True
    async_enabled: bool = True
    thread_pool_size: int = 4
    query_timeout: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_yaml_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_path}: {e}")


def get_settings() -> Settings:
    """Get application settings singleton."""
    if not hasattr(get_settings, '_instance'):
        get_settings._instance = Settings()
    return get_settings._instance


def validate_settings(settings: Settings) -> bool:
    """Validate critical settings are present."""
    errors = []

    if not settings.anthropic_api_key and settings.environment == "production":
        errors.append("ANTHROPIC_API_KEY is required in production")

    if settings.chunk_size < 10:
        errors.append("chunk_size must be at least 10")

    if settings.top_k < 1:
        errors.append("top_k must be at least 1")

    if settings.rate_limit_requests < 1:
        errors.append("rate_limit_requests must be at least 1")

    # Cache validation
    if settings.cache_l1_max_size <= 0:
        errors.append("cache_l1_max_size must be positive")

    if settings.cache_l2_max_size_mb <= 0:
        errors.append("cache_l2_max_size_mb must be positive")

    if settings.embedding_batch_size <= 0:
        errors.append("embedding_batch_size must be positive")

    if errors:
        raise ValueError(f"Settings validation failed:\n" + "\n".join(errors))

    return True
