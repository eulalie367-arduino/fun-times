# RAG Pipeline - Production-Ready Framework

A comprehensive, production-ready Retrieval-Augmented Generation (RAG) framework with built-in error handling, configuration management, logging, testing, and monitoring.

## Features

### Phase 1: Production Foundation ✅
- **Configuration Management**: YAML + environment variables
- **Error Handling**: Custom exceptions and graceful degradation
- **Logging**: Structured JSON logging with console and file output
- **Environment Setup**: .env configuration, requirements management
- **Basic Testing**: Unit tests for core modules
- **Resilience**: Retry logic with exponential backoff, circuit breaker pattern

### Phase 2: Coming Soon
- Vector database persistence (ChromaDB)
- Semantic search and retrieval
- LLM integration (Claude API)
- Prompt engineering templates
- Comprehensive test suite

### Phase 3+: Advanced Features
- Caching layer (Redis)
- Monitoring and metrics (Prometheus)
- Batch processing
- Data quality validation
- Multi-language support

## Quick Start

### Installation

```bash
# Clone the project
cd /d/rag-pipeline

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy example environment
cp .env.example .env

# Edit .env with your settings
# CRITICAL: Set ANTHROPIC_API_KEY before production use
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src
```

## Project Structure

```
rag-pipeline/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── app.py                # Application bootstrap
│   ├── config.py             # Configuration management
│   ├── exceptions.py         # Custom exceptions
│   ├── logger.py             # Structured logging
│   └── retry.py              # Resilience patterns
├── config/
│   └── settings.yaml         # Configuration templates
├── tests/
│   ├── test_config.py        # Config tests
│   └── test_retry.py         # Retry mechanism tests
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Configuration

### Environment Variables

All settings can be configured via environment variables (see `.env.example`):

```bash
ANTHROPIC_API_KEY=your_key_here
CHUNK_SIZE=512
TOP_K=5
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Settings File

Override defaults in `config/settings.yaml`:

```yaml
embedding:
  model: sentence-transformers/all-MiniLM-L6-v2
  batch_size: 32

chunking:
  size: 512
  overlap: 100

retrieval:
  top_k: 5
  similarity_threshold: 0.5
```

## Logging

The framework uses structured JSON logging for easy parsing and monitoring:

```python
from src.logger import get_logger

logger = get_logger(__name__)
logger.msg("custom_event", user_id=123, action="login")
```

Output:
```json
{
  "timestamp": "2026-05-28T10:30:00Z",
  "level": "info",
  "name": "src.module",
  "message": "custom_event",
  "user_id": 123,
  "action": "login"
}
```

## Error Handling

Custom exceptions for specific error types:

```python
from src.exceptions import RAGException, EmbeddingError, LLMError

try:
    # Your code
    pass
except EmbeddingError as e:
    logger.msg("embedding_failed", error=str(e))
except LLMError as e:
    logger.msg("llm_error", error=str(e))
except RAGException as e:
    logger.msg("rag_error", error=str(e))
```

## Resilience Patterns

### Retry with Exponential Backoff

```python
from src.retry import with_retry

@with_retry(max_attempts=3, initial_wait=1)
def call_external_api():
    # Automatically retries with backoff on failure
    pass
```

### Circuit Breaker

```python
from src.retry import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
try:
    result = breaker.call(risky_function)
except RAGException:
    # Circuit is open, handle gracefully
    pass
```

### Rate Limiting

```python
from src.retry import RateLimiter

limiter = RateLimiter(requests=100, window=3600)
if limiter.is_allowed():
    # Process request
    pass
```

## Application Initialization

```python
from src.app import RAGApplication

# Initialize with automatic config loading
app = RAGApplication()

# Get configuration
settings = app.get_settings()

# Get logger
logger = app.get_logger()

# Health check
health = app.health_check()
print(health)  # {"status": "healthy", "components": {...}}
```

## Testing

The framework includes comprehensive tests for all components:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_config.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_config.py::test_settings_defaults -v
```

## Best Practices

### Configuration
- ✅ Use `.env` for secrets and environment-specific settings
- ✅ Keep `config/settings.yaml` for defaults and templates
- ✅ Always validate settings on startup
- ✅ Never commit `.env` to git

### Error Handling
- ✅ Use specific exception types
- ✅ Log all errors with context
- ✅ Implement graceful degradation
- ✅ Use circuit breaker for external calls

### Logging
- ✅ Use structured logging (JSON format)
- ✅ Include relevant context in log messages
- ✅ Use appropriate log levels
- ✅ Monitor log files for errors

### Testing
- ✅ Write tests for critical functions
- ✅ Use fixtures for test data
- ✅ Test error paths, not just happy paths
- ✅ Maintain >80% code coverage

## Production Deployment

### Pre-deployment Checklist
- [ ] Set ANTHROPIC_API_KEY in secrets manager
- [ ] Configure log file path
- [ ] Set ENVIRONMENT=production
- [ ] Configure database connection
- [ ] Run full test suite
- [ ] Validate configuration
- [ ] Set up monitoring and alerting
- [ ] Document deployment procedure

### Health Check
```python
from src.app import get_app

app = get_app()
health = app.health_check()
if health["status"] == "healthy":
    # Ready for production
    pass
```

## Troubleshooting

### Missing API Key Error
```
ConfigurationError: ANTHROPIC_API_KEY is required in production
```
Solution: Set `ANTHROPIC_API_KEY` in `.env` or environment

### Configuration Validation Error
```
ValueError: Settings validation failed
```
Solution: Check `.env` values match required types in `src/config.py`

### Import Errors
```
ModuleNotFoundError: No module named 'src'
```
Solution: Run from project root: `cd /d/rag-pipeline`

## Roadmap

- [x] Phase 1: Configuration, errors, logging, testing
- [ ] Phase 2: Vector DB, retrieval, LLM integration
- [ ] Phase 3: Caching, monitoring, batch processing
- [ ] Phase 4: Advanced features, optimizations

## Contributing

When adding new features:
1. Create tests first (TDD)
2. Implement feature with error handling
3. Add logging for debugging
4. Update this README
5. Run full test suite before commit

## License

Proprietary - Anthropic

## Support

For issues or questions:
1. Check logs: `cat logs/rag.log`
2. Run health check: `python -c "from src.app import get_app; print(get_app().health_check())"`
3. Review error messages in test output
4. Check configuration in `.env`
