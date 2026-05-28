# Deployment Guide - RAG Pipeline

## Pre-Deployment Checklist

- [ ] All tests passing (`pytest tests/`)
- [ ] Configuration validated
- [ ] API keys set in secrets manager
- [ ] Log directory writable
- [ ] Database connection tested
- [ ] Health check passing
- [ ] Documentation updated

## Environment Setup

### Development
```bash
cp .env.example .env
# Edit .env with dev values
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true
```

### Staging
```bash
# Use secrets manager for API keys
export ANTHROPIC_API_KEY=$(aws secretsmanager get-secret-value --secret-id rag/api-key)
export ENVIRONMENT=staging
export LOG_LEVEL=INFO
export DEBUG=false
```

### Production
```bash
# Use secrets manager exclusively - NEVER in .env
export ANTHROPIC_API_KEY=$(aws secretsmanager get-secret-value --secret-id rag/api-key-prod)
export ENVIRONMENT=production
export LOG_LEVEL=WARN
export DEBUG=false
export CHROMADB_HOST=rag-db.internal
export CHROMADB_PORT=8000
```

## Installation & Setup

```bash
# Clone and navigate
git clone <repo-url>
cd rag-pipeline

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing

# Run tests
pytest tests/ -v

# Initialize application
python -c "from src.app import RAGApplication; app = RAGApplication(); print(app.health_check())"
```

## Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV LOG_FILE=/var/log/rag/app.log

RUN mkdir -p /var/log/rag /data/chroma

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.app import get_app; print(get_app().health_check())"

CMD ["python", "-m", "src.app"]
```

Build and run:
```bash
docker build -t rag-pipeline:1.0.0 .
docker run -e ANTHROPIC_API_KEY=$API_KEY \
           -v /data/chroma:/data/chroma \
           -v /var/log/rag:/var/log/rag \
           rag-pipeline:1.0.0
```

## Monitoring

### Health Checks
```bash
# Check application health
python -c "from src.app import get_app; import json; print(json.dumps(get_app().health_check(), indent=2))"
```

### Log Monitoring
```bash
# Follow logs in real-time
tail -f /var/log/rag/app.log | jq '.'

# Count errors
grep '"level":"error"' /var/log/rag/app.log | wc -l

# Extract error details
grep '"level":"error"' /var/log/rag/app.log | jq '.message, .error'
```

### Prometheus Metrics (Phase 2+)
```bash
# Access metrics on port 9090
curl http://localhost:9090/metrics
```

## Rollback Procedure

### If deployment fails:
1. Check logs: `tail -f /var/log/rag/app.log`
2. Review health check: See Health Checks section
3. Rollback to previous version:
   ```bash
   git revert HEAD
   pip install -r requirements.txt
   python -m src.app
   ```

### If database corruption:
1. Restore from backup:
   ```bash
   cp /backups/chroma-latest /data/chroma
   ```
2. Verify integrity with health check
3. Restart application

## Performance Tuning

### For High Load
```yaml
# config/settings.yaml
performance:
  batch_processing: true
  async_enabled: true
  thread_pool_size: 8      # Increase from 4

cache:
  enabled: true
  backend: redis           # Switch from memory
  redis_url: redis://prod:6379
```

### Database Optimization
```bash
# Monitor ChromaDB connections
chromadb-cli info

# Vacuum (cleanup)
chromadb-cli vacuum

# Index optimization (Phase 2+)
chromadb-cli optimize
```

## Security Hardening

### API Key Management
```bash
# Use environment variables, never commit to git
export ANTHROPIC_API_KEY=...

# Or use AWS Secrets Manager
export ANTHROPIC_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id rag/api-key \
  --query SecretString \
  --output text)
```

### Network Security
- [ ] Use HTTPS for all external APIs
- [ ] Firewall ChromaDB port (8000)
- [ ] Enable rate limiting (see config/settings.yaml)
- [ ] Use VPN/bastion for direct database access

### Logging & Audit
- [ ] Enable audit logging for all API calls
- [ ] Archive logs to S3/Cloud Storage
- [ ] Set up alerts for errors and failures
- [ ] Regular log review for security issues

## Troubleshooting

### Application won't start
```bash
# Check environment
env | grep RAG

# Check logs for errors
tail -100 /var/log/rag/app.log | jq '.level == "error"'

# Validate configuration
python -c "from src.config import get_settings; s = get_settings(); print(s)"
```

### High memory usage
```bash
# Check log rotation
ls -lh /var/log/rag/

# Monitor embeddings cache
# (Phase 2+) Adjust cache_embeddings: false in config

# Reduce thread pool size
# Edit config/settings.yaml: thread_pool_size: 2
```

### API key issues
```bash
# Verify key format
echo $ANTHROPIC_API_KEY | head -c 20

# Test API call
python -c "from anthropic import Anthropic; Anthropic().messages.create(model='claude-opus-4-6', messages=[{'role': 'user', 'content': 'test'}])"
```

## Support

For deployment issues:
1. Check logs: `/var/log/rag/app.log`
2. Run health check
3. Review DEPLOYMENT.md troubleshooting
4. Check git log for recent changes
5. Contact DevOps team with logs attached
