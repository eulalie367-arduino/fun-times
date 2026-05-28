# LLM Integration Guide - Phase 2 Step 3

Complete guide to the RAG system's Claude API integration and intelligent query capabilities.

## Overview

The LLM integration layer enables the RAG pipeline to:
- Query Claude API for intelligent responses with context
- Perform semantic search across multiple data collections
- Support complex persona-based queries
- Handle time-aware music recommendations
- Generate context-aware responses

## Architecture

### Components

```
RAGQueryHandler
├── ClaudeRAGClient (LLM communication)
├── EmbeddingGenerator (semantic encoding)
├── VectorStore (similarity search)
└── DocumentIngestionEngine (data loading)
```

### Data Flow

```
User Query
    ↓
[Embedding Generation]
    ↓
[Vector Store Search]
    ├── Movie Collection Search
    ├── Song Collection Search
    └── Document Collection Search
    ↓
[Context Assembly]
    ↓
[Claude API Query]
    ↓
[Response Generation]
    ↓
Result
```

## Core Classes

### ClaudeRAGClient

Handles Claude API communication with automatic fallback:

```python
from src.llm_integration import ClaudeRAGClient

# Initialize
client = ClaudeRAGClient(api_key="your-api-key")

# Query with context
response = client.query(
    prompt="What should I watch?",
    context="User prefers sci-fi movies",
    max_tokens=512
)
```

**Features:**
- Automatic API fallback when unavailable
- Structured logging of all queries
- Configurable token limits
- Context awareness

### RAGQueryHandler

Orchestrates complex RAG queries:

```python
from src.llm_integration import RAGQueryHandler

handler = RAGQueryHandler(
    vector_store=store,
    embedding_generator=embeddings,
    llm_client=client
)

# Find movies by persona
movies = handler.find_movie_by_persona("tech_enthusiast", top_k=5)

# Find songs by time
songs = handler.find_song_by_time("night", mood="energetic", top_k=3)

# Intelligent query
response = handler.intelligent_query(
    query="Recommend a movie for a programmer",
    context_docs=[],
    top_k=5
)
```

**Supported Queries:**
1. **Persona-Based Movie Search**
   - Input: User persona (e.g., "tech_enthusiast", "drama_lover")
   - Output: Ranked list of matching movies
   - Use case: User preference matching

2. **Time-Based Song Search**
   - Input: Time of day + optional mood
   - Output: Ranked list of suitable songs
   - Use case: Context-aware music recommendation

3. **Intelligent Multi-Source Query**
   - Input: Natural language query + context
   - Output: LLM response with retrieved context
   - Use case: Complex questions requiring synthesis

## Usage Examples

### Example 1: Movie Recommendation by Persona

```python
from src.rag_app import get_rag_pipeline

rag = get_rag_pipeline()

# Set up sample data
rag.setup_sample_data()

# Find movies for a tech enthusiast
movies = rag.find_movies_by_persona("tech_enthusiast", top_k=3)

for movie in movies:
    print(f"Title: {movie['title']}")
    print(f"Description: {movie['description'][:100]}...")
    print(f"Metadata: {movie['metadata']}")
```

**Output:**
```
Title: The Matrix
Description: A computer hacker learns about the true nature of reality...
Metadata: {'title': 'The Matrix', 'personas': 'tech_enthusiast,action_lover,...'}

Title: Inception
Description: A skilled thief who steals corporate secrets through dream-sharing...
Metadata: {'title': 'Inception', 'personas': 'sci-fi_fan,mind_bender,...'}
```

### Example 2: Song Recommendation by Time

```python
rag = get_rag_pipeline()
rag.setup_sample_data()

# Find songs for night time
songs = rag.find_songs_by_time("night", mood="energetic", top_k=2)

for song in songs:
    print(f"Title: {song['title']}")
    print(f"Artist: {song['artist']}")
    print(f"Best Time: {song['metadata'].get('best_time', 'N/A')}")
```

**Output:**
```
Title: Midnight City
Artist: M83
Best Time: night,party

Title: Bohemian Rhapsody
Artist: Queen
Best Time: evening,night
```

### Example 3: Intelligent Query with Context

```python
response = rag.query(
    query="What movie should a programmer watch tonight?",
    context_collections=["movies", "songs"],
    top_k=5
)

print(response)
```

## Data Integration

### Movie Data Structure

```json
{
  "id": "movie_001",
  "title": "The Matrix",
  "year": 1999,
  "genre": ["sci-fi", "action"],
  "description": "A computer hacker learns...",
  "director": "Lana Wachowski, Lilly Wachowski",
  "duration": 136,
  "personas": ["tech_enthusiast", "action_lover", "philosophical_thinker"],
  "rating": 8.7
}
```

### Song Data Structure

```json
{
  "id": "song_001",
  "title": "Bohemian Rhapsody",
  "artist": "Queen",
  "duration": 354,
  "year": 1975,
  "genre": ["rock", "opera"],
  "mood": ["epic", "theatrical", "complex"],
  "best_time": ["evening", "night"],
  "description": "A legendary six-minute epic rock opera..."
}
```

## Configuration

### Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_STORE_PATH=.chroma
LOG_LEVEL=INFO
```

### Application Settings

```python
# config/settings.yml
embeddings:
  model_name: all-MiniLM-L6-v2
  batch_size: 32
  cache_enabled: true

vector_store:
  persist_dir: .chroma
  cache_size: 10000

llm:
  model: claude-opus-4-6
  max_tokens: 1024
  timeout: 30
```

## Testing

### Unit Tests

```bash
# Run LLM integration tests
pytest tests/unit/test_rag_e2e.py::TestRAGEndToEnd -v

# Run specific test
pytest tests/unit/test_rag_e2e.py::TestRAGEndToEnd::test_find_movie_by_persona_tech_enthusiast -v
```

### Integration Tests

```bash
# Run complete workflow tests
pytest tests/unit/test_rag_e2e.py::TestRAGEndToEnd::test_complete_rag_workflow -v

# Run with context
pytest tests/unit/test_rag_e2e.py::TestRAGWithDocuments -v
```

### Test Coverage

**Currently Tested:**
- ✅ Movie ingestion and search (5 test cases)
- ✅ Song ingestion and search (4 test cases)
- ✅ Persona-based queries (3 test cases)
- ✅ Time-based queries (3 test cases)
- ✅ Intelligent multi-source queries (2 test cases)
- ✅ Error handling (3 test cases)
- ✅ Caching behavior (1 test case)
- ✅ Complete workflow (1 test case)

**Total: 22 test cases**

## Performance Characteristics

### Query Latency

| Operation | Latency | Notes |
|-----------|---------|-------|
| Movie search | 50-100ms | Cached if repeated |
| Song search | 50-100ms | Time-based optimization |
| Embedding generation | 10-50ms | Per-query cost |
| Claude API call | 500-2000ms | Network dependent |
| **Complete query** | **700-2500ms** | With all steps |

### Caching Strategy

**L1 Cache (Memory):**
- Query embeddings (LRU, 1000 entries)
- Search results (time: 5 minutes)

**L2 Cache (Disk):**
- Vector embeddings (persistent)
- Query history (30 days)

**L3 Cache (Vector Store):**
- ChromaDB collection (semantic cache)
- Automatic deduplication

## Error Handling

### Common Errors and Solutions

#### 1. API Key Not Found

```python
# Error
IngestError: No API key provided

# Solution
export ANTHROPIC_API_KEY=your-key
# or
client = ClaudeRAGClient(api_key="your-key")
```

#### 2. Collection Not Found

```python
# Error
Collection 'movies' not found

# Solution
rag.setup_sample_data()  # Ingest sample data first
```

#### 3. Embedding Generation Failed

```python
# Error
sentence-transformers download failed

# Solution
# Ensure sentence-transformers is installed
pip install sentence-transformers
# Or use cached model
EmbeddingGenerator(model_name="all-MiniLM-L6-v2", download=False)
```

#### 4. Vector Store Connection Failed

```python
# Error
ChromaDB connection error

# Solution
# Check persistence directory
ls -la .chroma/
# Or recreate
import shutil
shutil.rmtree(".chroma")
# Reingest data
rag.setup_sample_data()
```

## Advanced Features

### Custom Embedding Models

```python
from src.rag_app import RAGPipeline

rag = RAGPipeline(
    embedding_model="all-mpnet-base-v2"  # Larger model
)
```

### Batch Ingestion

```python
stats = rag.ingest_data_from_file(
    data_file="data/movies.json",
    collection_name="movies",
    document_field="description",
    metadata_fields=["title", "genre", "personas"]
)

print(f"Ingested {stats['successful']} documents")
```

### Custom Query Context

```python
response = rag.query(
    query="What should I watch?",
    context_collections=["movies", "documents"],
    top_k=10
)
```

## Integration Points

### With Document Ingestion (Phase 2 Step 2)

```python
# Ingest documents from files
rag.ingest_directory("documents/", collection_name="docs")

# Use in queries
response = rag.query(
    query="What does the document say about RAG?",
    context_collections=["docs"]
)
```

### With Vector Store (Phase 2 Step 1)

```python
# Leverage L1, L2, L3 caching
vector_store = rag.vector_store

# Direct access if needed
results = vector_store.search_with_cache(
    collection_name="movies",
    query_embeddings=[embedding],
    n_results=5
)
```

### With Embeddings

```python
# Custom embedding generation
embedding = rag.embedding_generator.embed_text(
    "A tech enthusiast looking for sci-fi"
)

# Batch embeddings
embeddings = rag.embedding_generator.embed_texts(
    ["text1", "text2", "text3"]
)
```

## Scaling Considerations

### For Production

1. **Caching**
   - Enable L2 disk cache
   - Use Redis for distributed cache
   - Implement query deduplication

2. **Parallelization**
   - Use ThreadPoolExecutor for batch queries
   - Parallel embedding generation
   - Parallel vector store searches

3. **Monitoring**
   - Track query latency
   - Monitor cache hit rates
   - Log API usage

4. **Cost Optimization**
   - Batch API calls
   - Cache common queries
   - Use smaller embedding models

## Troubleshooting

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

rag = RAGPipeline()
rag.health_check()  # Detailed diagnostics
```

### Health Check

```python
health = rag.health_check()
print(health)

# Output:
# {
#   "status": "healthy",
#   "components": {
#     "embeddings": "ok",
#     "vector_store": "ok",
#     "llm": "ok"
#   },
#   "collections": ["movies", "songs"]
# }
```

### Logging

All operations are logged with structured logging:

```bash
# View logs
tail -f logs/rag.log

# Search for errors
grep "error" logs/rag.log

# View specific operation
grep "intelligent_query" logs/rag.log
```

## Next Steps

1. **Expand Data Collections**
   - Add more movies with diverse personas
   - Add more songs with rich metadata
   - Ingest real documents for document QA

2. **Enhanced LLM Integration**
   - Support multiple LLM models
   - Implement streaming responses
   - Add multi-turn conversations

3. **Performance Optimization**
   - Implement vector search optimization
   - Add distributed caching
   - Optimize embedding batching

4. **Advanced Features**
   - Implement re-ranking
   - Add semantic filtering
   - Support multi-modal queries

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [SentenceTransformers](https://www.sbert.net/)
- [Claude API Documentation](https://docs.anthropic.com/)
- [Vector Search Fundamentals](https://en.wikipedia.org/wiki/Vector_space_model)

---

**RAG System powered by Claude, ChromaDB, and SentenceTransformers** 🚀
