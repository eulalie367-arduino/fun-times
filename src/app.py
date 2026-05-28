"""RAG Pipeline application bootstrap."""
import os
from pathlib import Path
from dotenv import load_dotenv
from src.config import get_settings, validate_settings
from src.logger import setup_logging, get_logger
from src.exceptions import ConfigurationError


class RAGApplication:
    """Main RAG Pipeline application."""

    def __init__(self, env_file: str = ".env"):
        """Initialize RAG application."""
        self.logger = None
        self.settings = None
        self._initialize(env_file)

    def _initialize(self, env_file: str):
        """Initialize application with configuration and logging."""

        # Load environment variables
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_file)
        else:
            self.logger = get_logger(__name__)
            self.logger.msg(
                "env_file_not_found",
                path=env_file,
                message="Using environment variables or defaults"
            )

        # Get settings
        self.settings = get_settings()

        # Validate settings
        try:
            validate_settings(self.settings)
        except ValueError as e:
            raise ConfigurationError(str(e))

        # Setup logging
        self.logger = setup_logging(
            log_level=self.settings.log_level,
            log_format=self.settings.log_format,
            log_file=self.settings.log_file,
            console_output=True
        )

        self.logger.info(
            "RAG Pipeline initialized",
            environment=self.settings.environment,
            version="1.0.0"
        )

    def get_settings(self):
        """Get application settings."""
        return self.settings

    def get_logger(self):
        """Get application logger."""
        return self.logger

    def health_check(self) -> dict:
        """Perform health check on application components."""
        health = {
            "status": "healthy",
            "components": {}
        }

        # Check configuration
        try:
            validate_settings(self.settings)
            health["components"]["config"] = "ok"
        except Exception as e:
            health["components"]["config"] = f"error: {e}"
            health["status"] = "unhealthy"

        # Check logging
        try:
            if self.logger:
                health["components"]["logging"] = "ok"
            else:
                health["components"]["logging"] = "error: logger not initialized"
                health["status"] = "unhealthy"
        except Exception as e:
            health["components"]["logging"] = f"error: {e}"
            health["status"] = "unhealthy"

        self.logger.msg("health_check", result=health)
        return health


# Global application instance
_app_instance = None


def get_app() -> RAGApplication:
    """Get or create global RAG application instance."""
    global _app_instance
    if _app_instance is None:
        _app_instance = RAGApplication()
    return _app_instance
