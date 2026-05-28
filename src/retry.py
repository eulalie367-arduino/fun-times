"""Retry logic with exponential backoff."""
import time
import functools
from typing import Callable, Type, Tuple, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)
from src.logger import get_logger
from src.exceptions import RAGException


logger = get_logger(__name__)


def with_retry(
    max_attempts: int = 3,
    initial_wait: float = 1,
    max_wait: float = 30,
    exponential_base: float = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator for automatic retry with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=initial_wait,
                min=initial_wait,
                max=max_wait
            ),
            retry=retry_if_exception_type(exceptions),
            before=before_log(logger, "warning"),
            after=after_log(logger, "info")
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1,
    max_delay: float = 30,
    backoff_factor: float = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> any:
    """Manually retry a function with exponential backoff."""

    last_exception = None
    delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            logger.msg(
                "retry_attempt",
                function=func.__name__,
                attempt=attempt,
                max_attempts=max_attempts
            )
            return func()
        except exceptions as e:
            last_exception = e

            if attempt == max_attempts:
                logger.msg(
                    "retry_exhausted",
                    function=func.__name__,
                    attempts=max_attempts,
                    error=str(e)
                )
                raise

            # Wait before retry
            wait_time = min(delay, max_delay)
            logger.msg(
                "retry_waiting",
                function=func.__name__,
                delay_seconds=wait_time,
                attempt=attempt
            )
            time.sleep(wait_time)
            delay *= backoff_factor

    if last_exception:
        raise last_exception


class CircuitBreaker:
    """Circuit breaker pattern for API calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""

        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                logger.msg(
                    "circuit_breaker_half_open",
                    service=func.__name__
                )
            else:
                raise RAGException(
                    f"Circuit breaker open for {func.__name__}. "
                    f"Service unavailable."
                )

        try:
            result = func(*args, **kwargs)

            if self.state == "half_open":
                self._reset()
                logger.msg(
                    "circuit_breaker_closed",
                    service=func.__name__
                )

            return result

        except self.expected_exception as e:
            self._record_failure()
            logger.msg(
                "circuit_breaker_failure",
                service=func.__name__,
                failure_count=self.failure_count,
                error=str(e)
            )

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.msg(
                    "circuit_breaker_open",
                    service=func.__name__,
                    threshold=self.failure_threshold
                )

            raise

    def _record_failure(self):
        """Record a failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()

    def _reset(self):
        """Reset circuit breaker to closed state."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.recovery_timeout


class RateLimiter:
    """Rate limiter using token bucket algorithm."""

    def __init__(self, requests: int, window: int):
        """
        Initialize rate limiter.

        Args:
            requests: Number of requests allowed
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self.tokens = requests
        self.last_reset = time.time()

    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        now = time.time()
        time_passed = now - self.last_reset

        if time_passed >= self.window:
            self.tokens = self.requests
            self.last_reset = now

        if self.tokens > 0:
            self.tokens -= 1
            return True

        return False

    def wait_if_needed(self):
        """Wait until request is allowed."""
        while not self.is_allowed():
            time.sleep(0.1)
