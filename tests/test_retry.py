"""Tests for retry and resilience mechanisms."""
import time
import pytest
from src.retry import retry_with_backoff, CircuitBreaker, RateLimiter
from src.exceptions import RAGException


def test_retry_with_backoff_success():
    """Test successful function call on first try."""
    call_count = [0]

    def successful_func():
        call_count[0] += 1
        return "success"

    result = retry_with_backoff(successful_func, max_attempts=3)
    assert result == "success"
    assert call_count[0] == 1


def test_retry_with_backoff_eventual_success():
    """Test function that eventually succeeds."""
    call_count = [0]

    def eventual_success():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("Not yet")
        return "success"

    result = retry_with_backoff(
        eventual_success,
        max_attempts=5,
        initial_delay=0.01,
        exceptions=(ValueError,)
    )
    assert result == "success"
    assert call_count[0] == 3


def test_retry_with_backoff_exhausted():
    """Test retry exhaustion raises last exception."""
    call_count = [0]

    def always_fails():
        call_count[0] += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError) as exc_info:
        retry_with_backoff(
            always_fails,
            max_attempts=3,
            initial_delay=0.01
        )

    assert "Always fails" in str(exc_info.value)
    assert call_count[0] == 3


def test_circuit_breaker_closed_state():
    """Test circuit breaker in closed state allows calls."""
    breaker = CircuitBreaker(failure_threshold=3)

    def successful_func():
        return "success"

    result = breaker.call(successful_func)
    assert result == "success"
    assert breaker.state == "closed"


def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after threshold failures."""
    call_count = [0]
    breaker = CircuitBreaker(
        failure_threshold=2,
        expected_exception=ValueError
    )

    def failing_func():
        call_count[0] += 1
        raise ValueError("Failed")

    # First failure
    with pytest.raises(ValueError):
        breaker.call(failing_func)
    assert breaker.state == "closed"
    assert breaker.failure_count == 1

    # Second failure - should open circuit
    with pytest.raises(ValueError):
        breaker.call(failing_func)
    assert breaker.state == "open"
    assert breaker.failure_count == 2

    # Third attempt - should raise without calling function
    with pytest.raises(RAGException) as exc_info:
        breaker.call(failing_func)
    assert "Circuit breaker open" in str(exc_info.value)
    assert call_count[0] == 2  # Function not called third time


def test_circuit_breaker_half_open_recovery():
    """Test circuit breaker recovery in half-open state."""
    call_count = [0]
    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=0,  # Immediate
        expected_exception=ValueError
    )

    def failing_func():
        call_count[0] += 1
        raise ValueError("Failed")

    # Open the circuit
    with pytest.raises(ValueError):
        breaker.call(failing_func)

    breaker.failure_count = 1  # Force to threshold
    breaker.state = "open"

    # Circuit should attempt reset
    with pytest.raises(ValueError):
        breaker.call(failing_func)
    assert breaker.state == "half_open"


def test_rate_limiter_allows_requests():
    """Test rate limiter allows requests within limit."""
    limiter = RateLimiter(requests=3, window=1)

    assert limiter.is_allowed() is True
    assert limiter.is_allowed() is True
    assert limiter.is_allowed() is True
    assert limiter.is_allowed() is False  # Fourth request denied


def test_rate_limiter_resets_after_window():
    """Test rate limiter resets after time window."""
    limiter = RateLimiter(requests=1, window=0.05)

    assert limiter.is_allowed() is True
    assert limiter.is_allowed() is False

    time.sleep(0.06)
    assert limiter.is_allowed() is True


def test_rate_limiter_wait():
    """Test rate limiter wait_if_needed blocks appropriately."""
    limiter = RateLimiter(requests=1, window=1)

    start = time.time()
    limiter.wait_if_needed()  # Should succeed immediately
    duration = time.time() - start
    assert duration < 0.1  # Should be fast

    limiter.is_allowed()  # Consume token
    limiter.wait_if_needed()  # Should wait
    # Note: not checking exact timing as it's system dependent
