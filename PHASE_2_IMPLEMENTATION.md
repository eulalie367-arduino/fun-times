# Phase 2 Implementation Guide - RAG Pipeline

**Branch:** `feature/phase-2`
**Status:** In Progress
**Timeline:** 2-2.5 weeks
**Target:** Production-ready RAG system

---

## Step-by-Step Implementation

Each step includes:
- Detailed specifications
- Test-driven development approach
- Git commit instructions
- Success criteria

### ✅ Step 1: Vector Store Integration

**File:** `src/vector_store.py`
**Lines:** ~300 | **Tests:** `tests/unit/test_vector_store.py` (~200 lines)

#### Implementation Checklist
- [ ] Create `VectorStore` class with ChromaDB wrapper
- [ ] Implement connection pooling and retry logic
- [ ] Add collection management (create, delete, list)
- [ ] Implement CRUD operations (add, search, delete, update)
- [ ] Add metadata filtering support
- [ ] Implement health checks
- [ ] Write comprehensive unit tests
- [ ] Test error scenarios (connection failures, timeouts)

#### Key Methods
```python
class VectorStore:
    def __init__(self, path, host, port, mode)
    def get_or_create_client()
    def create_collection(name, metadata)
    def add_vectors(documents, embeddings, metadatas, ids)
    def search(embeddings, top_k, where_filter)
    def delete(ids)
    def update(ids, documents, embeddings)
    def health_check()
    def get_stats()
```

#### Success Criteria
- [x] Collections persist to disk
- [x] Search returns correct results
- [x] Metadata filtering works
- [x] Connection retries work
- [x] All unit tests pass (200+ lines)

#### Git Commit
```bash
git add src/vector_store.py tests/unit/test_vector_store.py
git commit -m "feat: Add vector store integration with ChromaDB persistence

- Implement VectorStore wrapper for ChromaDB
- Add connection pooling with retry logic
- Implement CRUD operations for vectors
- Add metadata filtering support
- Write comprehensive unit tests
- Handle connection errors gracefully"
```

---

### ✅ Step 2: Embedding Generation

**File:** `src/embeddings.py`
**Lines:** ~350 | **Tests:** `tests/unit/test_embeddings.py` (~250 lines)

#### Implementation Checklist
- [ ] Create `EmbeddingGenerator` class with SentenceTransformer
- [ ] Implement batch embedding generation
- [ ] Add in-memory caching layer
- [ ] Implement Redis caching (optional backend)
- [ ] Add device management (GPU/CPU auto-detection)
- [ ] Implement embedding normalization
- [ ] Add cache statistics and monitoring
- [ ] Write comprehensive unit tests

#### Key Methods
```python
class EmbeddingGenerator:
    def __init__(model_name, device, batch_size)
    def embed_text(texts)
    def embed_batch(texts, batch_size)
    def embed_single(text)

class EmbeddingCache:
    def get(key)
    def set(key, embedding)
    def clear()
    def stats()
```

#### Success Criteria
- [x] Generates correct embeddings
- [x] Batch processing works efficiently
- [x] Caching reduces redundant computations
- [x] Device selection works (GPU if available)
- [x] All unit tests pass (250+ lines)

#### Git Commit
```bash
git add src/embeddings.py tests/unit/test_embeddings.py
git commit -m "feat: Add embedding generation with caching

- Implement EmbeddingGenerator with batch processing
- Add in-memory cache with TTL support
- Implement optional Redis backend
- Auto-detect GPU/CPU device
- Normalize embeddings for consistency
- Add cache statistics and monitoring
- Write comprehensive unit tests"
```

---

### ✅ Step 3: Document Ingestion

**File:** `src/ingestion.py`
**Lines:** ~400 | **Tests:** `tests/unit/test_ingestion.py` (~300 lines)

#### Implementation Checklist
- [ ] Create `DocumentChunker` class
- [ ] Implement configurable chunking strategies (fixed, sliding, semantic)
- [ ] Add support for multiple formats (txt, md, pdf, code)
- [ ] Implement metadata extraction
- [ ] Add chunk validation (length, quality)
- [ ] Implement duplicate detection
- [ ] Add batch ingestion with progress tracking
- [ ] Write comprehensive unit tests

#### Key Methods
```python
class DocumentChunker:
    def chunk_text(text, size, overlap)
    def chunk_markdown(markdown)
    def chunk_code(code, language)
    def validate_chunks()

class DocumentIngestor:
    def ingest_file(path)
    def ingest_files_batch(paths)
    def ingest_directory(path, pattern)
```

#### Success Criteria
- [x] Chunks created with correct size/overlap
- [x] Multiple formats handled correctly
- [x] Metadata extracted properly
- [x] Duplicates detected and removed
- [x] Batch processing with progress
- [x] All unit tests pass (300+ lines)

#### Git Commit
```bash
git add src/ingestion.py tests/unit/test_ingestion.py
git commit -m "feat: Add document ingestion with chunking

- Implement DocumentChunker with multiple strategies
- Add support for txt, md, pdf, code formats
- Extract metadata (source, timestamp, etc.)
- Implement chunk validation and quality scoring
- Add duplicate detection across chunks
- Batch ingestion with progress tracking
- Write comprehensive unit tests"
```

---

### ✅ Step 4: Semantic Retrieval

**File:** `src/retrieval.py`
**Lines:** ~300 | **Tests:** `tests/unit/test_retrieval.py` (~250 lines)

#### Implementation Checklist
- [ ] Create `Retriever` class for semantic search
- [ ] Implement result deduplication
- [ ] Add optional reranking support
- [ ] Implement confidence scoring
- [ ] Add metadata filtering
- [ ] Implement result caching
- [ ] Add ranking and sorting options
- [ ] Write comprehensive unit tests

#### Key Methods
```python
class Retriever:
    def retrieve(query, top_k, filters)
    def rerank(results, scorer)
    def deduplicate(results)
    def score_results(results)

class ResultDeduplicator:
    def deduplicate(results)
    def remove_near_duplicates(results, threshold)
```

#### Success Criteria
- [x] Semantic search returns relevant results
- [x] Deduplication works correctly
- [x] Confidence scores accurate
- [x] Metadata filtering works
- [x] Caching reduces redundant queries
- [x] All unit tests pass (250+ lines)

#### Git Commit
```bash
git add src/retrieval.py tests/unit/test_retrieval.py
git commit -m "feat: Add semantic search and retrieval

- Implement Retriever for semantic search
- Add result deduplication with threshold
- Implement optional cross-encoder reranking
- Add confidence scoring system
- Support metadata filtering
- Implement result caching
- Ranking and sorting options
- Write comprehensive unit tests"
```

---

### ✅ Step 5: LLM Integration

**File:** `src/llm.py`
**Lines:** ~350 | **Tests:** `tests/unit/test_llm.py` (~200 lines)

#### Implementation Checklist
- [ ] Create `LLMClient` class for Claude API
- [ ] Implement streaming support
- [ ] Add token counting functionality
- [ ] Implement error handling (rate limits, timeouts)
- [ ] Use retry logic from Phase 1
- [ ] Add response caching
- [ ] Implement cost tracking
- [ ] Write comprehensive unit tests

#### Key Methods
```python
class LLMClient:
    def __init__(model, api_key, timeout)
    def complete(messages, temperature, max_tokens)
    def stream(messages)
    def count_tokens(text)

class LLMCache:
    def get(prompt_hash)
    def set(prompt_hash, response)
    def clear_expired()
```

#### Success Criteria
- [x] API calls work correctly
- [x] Streaming produces correct output
- [x] Token counting accurate
- [x] Rate limits handled gracefully
- [x] Response caching works
- [x] Error recovery functional
- [x] All unit tests pass (200+ lines)

#### Git Commit
```bash
git add src/llm.py tests/unit/test_llm.py
git commit -m "feat: Add LLM integration with Claude API

- Implement LLMClient for Claude API calls
- Add streaming support for real-time responses
- Implement token counting and cost tracking
- Use circuit breaker and retry from Phase 1
- Add response caching with TTL
- Handle rate limits and timeouts gracefully
- Write comprehensive unit tests"
```

---

### ✅ Step 6: Prompt Engineering

**File:** `src/prompts.py`
**Lines:** ~250 | **Tests:** `tests/unit/test_prompts.py` (~200 lines)

#### Implementation Checklist
- [ ] Create `PromptTemplate` class
- [ ] Implement task-specific templates (QA, code, analysis)
- [ ] Add context injection and ranking
- [ ] Implement few-shot example handling
- [ ] Add token counting before API calls
- [ ] Implement prompt validation
- [ ] Add customization options
- [ ] Write comprehensive unit tests

#### Key Methods
```python
class PromptTemplate:
    def __init__(template, input_variables)
    def format(**kwargs)
    def validate_inputs(**kwargs)

class PromptBuilder:
    def build_qa_prompt(query, context)
    def build_code_prompt(query, context)
    def build_analysis_prompt(query, context)
    def build_custom_prompt(template, variables)
```

#### Success Criteria
- [x] Templates format correctly
- [x] Context injected properly
- [x] Token counting accurate
- [x] Examples included correctly
- [x] Validation catches errors
- [x] Multiple task types supported
- [x] All unit tests pass (200+ lines)

#### Git Commit
```bash
git add src/prompts.py tests/unit/test_prompts.py
git commit -m "feat: Add prompt building and engineering

- Implement PromptTemplate system
- Add task-specific templates (QA, code, analysis)
- Implement context ranking and injection
- Add few-shot example handling
- Integrate token counting before API calls
- Add prompt validation and sanitization
- Support customization options
- Write comprehensive unit tests"
```

---

### ✅ Step 7: RAG Pipeline Orchestration

**File:** `src/rag.py`
**Lines:** ~250 | **Tests:** `tests/integration/test_rag_integration.py` (~300 lines)

#### Implementation Checklist
- [ ] Create `RAGPipeline` class orchestrating all components
- [ ] Implement end-to-end query execution
- [ ] Add streaming response support
- [ ] Implement performance tracking
- [ ] Add error recovery and fallbacks
- [ ] Implement feedback collection
- [ ] Add metrics collection
- [ ] Write comprehensive integration tests

#### Key Methods
```python
class RAGPipeline:
    def __init__(embedding_gen, vector_store, llm_client)
    def ingest_documents(documents)
    def query(question, top_k)
    def chat(messages)
    def stream(question)

class RAGResponse:
    response: str
    sources: List[Source]
    confidence: float
    tokens_used: int
    generation_time: float
```

#### Success Criteria
- [x] End-to-end pipeline works
- [x] Ingestion → Retrieval → Generation flow complete
- [x] Streaming responses functional
- [x] Performance metrics collected
- [x] Error recovery working
- [x] Response quality good
- [x] All integration tests pass (300+ lines)

#### Git Commit
```bash
git add src/rag.py tests/integration/test_rag_integration.py
git commit -m "feat: Add RAG pipeline orchestration

- Implement RAGPipeline orchestrating all components
- Add end-to-end query execution flow
- Implement streaming response support
- Add performance metrics collection
- Implement error recovery and fallbacks
- Add feedback collection mechanism
- Support both single query and chat interfaces
- Write comprehensive integration tests"
```

---

### ✅ Step 8: Integration Tests & Documentation

**Files:** `tests/`, `README.md`, `docs/`
**Lines:** ~1700 tests + docs

#### Implementation Checklist
- [ ] Write integration test suite
- [ ] Test end-to-end pipeline
- [ ] Add performance benchmarks
- [ ] Create test fixtures and data
- [ ] Update README with Phase 2 features
- [ ] Create API documentation
- [ ] Add usage examples
- [ ] Update DEPLOYMENT guide
- [ ] Add troubleshooting guide

#### Test Coverage Targets
- Unit tests: 90% coverage
- Integration tests: 85% coverage
- Overall: 85%+ coverage

#### Documentation Updates
- API reference for all new modules
- Usage examples for RAG pipeline
- Architecture diagrams
- Performance benchmarks
- Troubleshooting guide

#### Git Commit
```bash
git add tests/ README.md docs/
git commit -m "docs: Update documentation and add integration tests

- Add comprehensive integration test suite
- Add end-to-end pipeline tests
- Include performance benchmarks
- Create test fixtures and sample data
- Update README with Phase 2 features
- Add API documentation for new modules
- Include usage examples and tutorials
- Update deployment guide
- Add troubleshooting section"
```

---

## Running the Implementation

### Manual Step Execution

```bash
# For each step:
1. Implement the module (use PHASE_2_ROADMAP.md for specs)
2. Write tests following TDD
3. Run tests: pytest tests/ --cov=src
4. Run linting: flake8 src/
5. Commit with the message above
6. Update .aider-pipeline/task-phase-2-state.json
```

### Using aider with Implementation

For each component:
```bash
aider src/vector_store.py --read PHASE_2_ROADMAP.md \
  --message "Implement VectorStore class from Phase 2 spec"
```

---

## Monitoring Progress

Check current status:
```bash
cat .aider-pipeline/task-phase-2-state.json | jq '.metrics'
```

View step details:
```bash
cat .aider-pipeline/task-phase-2-state.json | jq '.steps[] | {name, status}'
```

---

## Success Criteria for Phase 2

✅ **All Components Implemented**
- [ ] Vector store with persistence
- [ ] Embedding generation with caching
- [ ] Document ingestion with chunking
- [ ] Semantic retrieval with ranking
- [ ] LLM integration with Claude API
- [ ] Prompt engineering system
- [ ] RAG pipeline orchestration

✅ **Testing Complete**
- [ ] Unit tests for all modules (90%+ coverage)
- [ ] Integration tests for pipeline (85%+ coverage)
- [ ] Performance benchmarks established
- [ ] Error scenarios tested

✅ **Documentation Complete**
- [ ] API documentation
- [ ] Usage examples
- [ ] Architecture diagrams
- [ ] Deployment updates
- [ ] Troubleshooting guide

✅ **Performance Targets Met**
- [ ] Embedding: <50ms per document
- [ ] Retrieval: <100ms per query
- [ ] LLM response: <5s end-to-end
- [ ] Handle 1000+ documents

---

## When Phase 2 is Complete

1. **Merge to main:**
   ```bash
   git checkout master
   git pull
   git merge feature/phase-2
   git push origin master
   ```

2. **Create Release Tag:**
   ```bash
   git tag -a v2.0.0 -m "RAG Pipeline Phase 2 - Full system"
   git push origin v2.0.0
   ```

3. **Prepare Phase 3:**
   - Performance optimization
   - Monitoring and metrics
   - Advanced features

---

## Quick Reference

| Step | Module | Lines | Tests | Days |
|------|--------|-------|-------|------|
| 1 | vector_store.py | 300 | 200 | 1.5 |
| 2 | embeddings.py | 350 | 250 | 1.5 |
| 3 | ingestion.py | 400 | 300 | 2.0 |
| 4 | retrieval.py | 300 | 250 | 1.5 |
| 5 | llm.py | 350 | 200 | 1.5 |
| 6 | prompts.py | 250 | 200 | 1.5 |
| 7 | rag.py | 250 | 300 | 2.0 |
| 8 | tests/docs | 1700 | - | 1.0 |
| **TOTAL** | | **2,700** | **1,700** | **13** |

---

**Status:** Ready for implementation
**Branch:** `feature/phase-2`
**Estimated Completion:** 2-2.5 weeks from start
