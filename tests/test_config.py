"""Tests for configuration management."""
import pytest
from src.config import Settings, validate_settings, get_settings
from src.exceptions import ConfigurationError


def test_settings_defaults():
    """Test settings have sensible defaults."""
    settings = Settings()
    assert settings.project_name == "RAG Pipeline"
    assert settings.chunk_size == 512
    assert settings.top_k == 5
    assert settings.environment == "development"


def test_settings_from_env(monkeypatch):
    """Test settings can be loaded from environment variables."""
    monkeypatch.setenv("CHUNK_SIZE", "256")
    monkeypatch.setenv("TOP_K", "10")

    settings = Settings()
    assert settings.chunk_size == 256
    assert settings.top_k == 10


def test_validate_settings_valid():
    """Test validation of valid settings."""
    settings = Settings(
        environment="development",
        chunk_size=512,
        top_k=5
    )
    assert validate_settings(settings) is True


def test_validate_settings_invalid_chunk_size():
    """Test validation fails for invalid chunk size."""
    settings = Settings(chunk_size=5)

    with pytest.raises(ValueError) as exc_info:
        validate_settings(settings)

    assert "chunk_size must be at least 10" in str(exc_info.value)


def test_validate_settings_missing_api_key():
    """Test validation requires API key in production."""
    settings = Settings(
        environment="production",
        anthropic_api_key=""
    )

    with pytest.raises(ValueError) as exc_info:
        validate_settings(settings)

    assert "ANTHROPIC_API_KEY is required" in str(exc_info.value)


def test_settings_singleton():
    """Test get_settings returns singleton."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_settings_pydantic_validation():
    """Test Pydantic validation for settings."""
    # Valid setting should not raise
    settings = Settings(rate_limit_requests=100)
    assert settings.rate_limit_requests == 100

    # Invalid types should be coerced if possible
    settings = Settings(rate_limit_requests="50")
    assert settings.rate_limit_requests == 50
