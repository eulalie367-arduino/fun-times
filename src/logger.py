"""Structured logging for RAG pipeline."""
import logging
import json
from pathlib import Path
from typing import Optional
import structlog
from pythonjsonlogger import jsonlogger


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """Configure structured logging for the application."""

    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    root_logger.handlers.clear()

    # JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s',
        defaults={'environment': 'production'}
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))

        if log_format == "json":
            console_handler.setFormatter(json_formatter)
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecimalEncoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return logging.getLogger(__name__)


def get_logger(name: str) -> structlog.PrintLogger:
    """Get a structlog logger instance."""
    return structlog.get_logger(name)


class LogContextManager:
    """Context manager for logging operation context."""

    def __init__(self, logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context

    def __enter__(self):
        self.logger.msg(
            "operation_start",
            operation=self.operation,
            **self.context
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.msg(
                "operation_error",
                operation=self.operation,
                error=str(exc_val),
                **self.context
            )
            return False

        self.logger.msg(
            "operation_complete",
            operation=self.operation,
            **self.context
        )
        return True


def log_performance(func):
    """Decorator to log function performance."""
    import time
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(__name__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.msg(
                "function_call",
                function=func.__name__,
                duration_seconds=duration,
                status="success"
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.msg(
                "function_call",
                function=func.__name__,
                duration_seconds=duration,
                status="error",
                error=str(e)
            )
            raise

    return wrapper
