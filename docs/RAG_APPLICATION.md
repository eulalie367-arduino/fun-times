# RAG Application Guide

Complete guide to using the RAGPipeline application for end-to-end RAG workflows.

## Quick Start

```python
from src.rag_app import RAGPipeline

# Create pipeline
rag = RAGPipeline()

# Load sample data
rag.setup_sample_data()

# Find movies by persona
movies = rag.find_movies_by_persona("tech_enthusiast", top_k=5)
for movie in movies:
    print(f"- {movie['title']}: {movie['description'][:80]}...")

# Find songs by time
songs = rag.find_songs_by_time("night", mood="energetic", top_k=3)
for song in songs:
    print(f"- {song['title']} by {song['artist']}")

# Intelligent query
response = rag.query("What should I watch tonight?", top_k=5)
print(response)
```

## API Reference

### RAGPipeline Class

Main orchestrator for the complete RAG system.

#### Initialization

```python
RAGPipeline(
    vector_store_path: str = ".chroma",
    embedding_model: str = "all-MiniLM-L6-v2",
    api_key: Optional[str] = None
)
```

**Parameters:**
- `vector_store_path`: ChromaDB storage directory (default: `.chroma`)
- `embedding_model`: SentenceTransformer model name (default: `all-MiniLM-L6-v2`)
- `api_key`: Anthropic API key (optional, uses env variable if not provided)

#### Methods

##### `ingest_data_from_file()`

Ingest data from JSON file into vector store.

```python
stats = rag.ingest_data_from_file(
    data_file="data/movies.json",
    collection_name="movies",
    document_field="description",
    metadata_fields=["title", "genre", "personas", "rating"]
)

print(f"Ingested {stats['successful']} documents")
```

**Returns:**
```python
{
    "total": 5,
    "successful": 5,
    "failed": 0
}
```

##### `ingest_directory()`

Ingest documents from a directory.

```python
stats = rag.ingest_directory(
    directory="documents/",
    collection_name="documents"
)
```

##### `find_movies_by_persona()`

Find movies matching a user persona.

```python
movies = rag.find_movies_by_persona(
    persona="tech_enthusiast",
    top_k=5
)
```

**Returns:**
```python
[
    {
        "id": "movie_001",
        "title": "The Matrix",
        "description": "A computer hacker learns...",
        "metadata": {
            "title": "The Matrix",
            "genre": "sci-fi,action",
            "personas": "tech_enthusiast,action_lover",
            "rating": 8.7
        }
    },
    # ... more results
]
```

##### `find_songs_by_time()`

Find songs suitable for a specific time.

```python
songs = rag.find_songs_by_time(
    time_of_day="night",
    mood="energetic",
    top_k=5
)
```

**Parameters:**
- `time_of_day`: Time period (morning, afternoon, evening, night)
- `mood`: Optional mood preference
- `top_k`: Number of results

**Returns:**
```python
[
    {
        "id": "song_001",
        "title": "Midnight City",
        "artist": "M83",
        "description": "An electronic anthem...",
        "metadata": {
            "title": "Midnight City",
            "artist": "M83",
            "genre": "synth-pop,electronic",
            "mood": "upbeat,energetic,nostalgic",
            "best_time": "night,party"
        }
    },
    # ... more results
]
```

##### `query()`

Execute intelligent query with context from vector store.

```python
response = rag.query(
    query="What movie should a programmer watch?",
    context_collections=["movies"],
    top_k=5
)
```

**Parameters:**
- `query`: User query string
- `context_collections`: Collections to search (optional)
- `top_k`: Number of results per collection

**Returns:**
```
"Based on the retrieved context, I recommend The Matrix for a programmer. It explores fundamental concepts about reality and technology in a compelling sci-fi narrative..."
```

##### `setup_sample_data()`

Load sample movie and song data.

```python
rag.setup_sample_data()
# Downloads and ingests data/movies.json and data/songs.json
```

##### `health_check()`

Check RAG system health.

```python
health = rag.health_check()
print(health)

# Output:
{
    "status": "healthy",
    "components": {
        "embeddings": "ok",
        "vector_store": "ok",
        "llm": "ok"
    },
    "collections": ["movies", "songs"]
}
```

## Usage Patterns

### Pattern 1: Movie Discovery

```python
# Find movies for different personas
personas = ["tech_enthusiast", "drama_lover", "animation_lover"]

for persona in personas:
    movies = rag.find_movies_by_persona(persona, top_k=3)
    print(f"\n{persona.replace('_', ' ').title()}:")
    for movie in movies:
        print(f"  - {movie['title']} ({movie['metadata'].get('rating', 'N/A')})")
```

### Pattern 2: Music Recommendation by Time

```python
# Recommend songs for different times
times = ["morning", "afternoon", "evening", "night"]
mood = "relaxing"

for time in times:
    songs = rag.find_songs_by_time(time, mood=mood, top_k=2)
    print(f"\n{time.title()} ({mood}):")
    for song in songs:
        print(f"  - {song['title']} by {song['artist']}")
```

### Pattern 3: Complex Query

```python
# Create a sophisticated query combining multiple factors
query = "I'm a tech enthusiast who wants to watch something intellectually stimulating tonight"
response = rag.query(query, context_collections=["movies"], top_k=10)
print(response)
```

### Pattern 4: Combined Recommendations

```python
# Recommend movie and music for an evening
movie = rag.find_movies_by_persona("intellectual_viewer", top_k=1)[0]
songs = rag.find_songs_by_time("evening", mood="contemplative", top_k=3)

print("Evening Plan:")
print(f"Movie: {movie['title']}")
print("Soundtrack:")
for song in songs:
    print(f"  - {song['title']}")
```

## Integration Examples

### With Flask Web Application

```python
from flask import Flask, request, jsonify
from src.rag_app import get_rag_pipeline

app = Flask(__name__)
rag = get_rag_pipeline()
rag.setup_sample_data()

@app.route("/api/movies", methods=["GET"])
def recommend_movies():
    persona = request.args.get("persona", "tech_enthusiast")
    top_k = request.args.get("top_k", 5, type=int)

    movies = rag.find_movies_by_persona(persona, top_k=top_k)
    return jsonify(movies)

@app.route("/api/songs", methods=["GET"])
def recommend_songs():
    time = request.args.get("time", "night")
    mood = request.args.get("mood", None)
    top_k = request.args.get("top_k", 5, type=int)

    songs = rag.find_songs_by_time(time, mood=mood, top_k=top_k)
    return jsonify(songs)

@app.route("/api/query", methods=["POST"])
def query():
    data = request.get_json()
    response = rag.query(data["query"], top_k=data.get("top_k", 5))
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
```

### With CLI Application

```python
import argparse
from src.rag_app import get_rag_pipeline

def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Movie command
    movies_parser = subparsers.add_parser("movies")
    movies_parser.add_argument("--persona", default="tech_enthusiast")
    movies_parser.add_argument("--top-k", type=int, default=5)

    # Song command
    songs_parser = subparsers.add_parser("songs")
    songs_parser.add_argument("--time", default="night")
    songs_parser.add_argument("--mood", default=None)
    songs_parser.add_argument("--top-k", type=int, default=5)

    # Query command
    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("query")
    query_parser.add_argument("--top-k", type=int, default=5)

    args = parser.parse_args()
    rag = get_rag_pipeline()
    rag.setup_sample_data()

    if args.command == "movies":
        movies = rag.find_movies_by_persona(args.persona, top_k=args.top_k)
        for movie in movies:
            print(f"- {movie['title']}: {movie['metadata']}")

    elif args.command == "songs":
        songs = rag.find_songs_by_time(args.time, mood=args.mood, top_k=args.top_k)
        for song in songs:
            print(f"- {song['title']} by {song['artist']}")

    elif args.command == "query":
        response = rag.query(args.query, top_k=args.top_k)
        print(response)

if __name__ == "__main__":
    main()
```

## Testing

### Unit Tests

```python
import pytest
from src.rag_app import RAGPipeline

def test_movie_discovery():
    rag = RAGPipeline()
    rag.setup_sample_data()

    movies = rag.find_movies_by_persona("tech_enthusiast", top_k=3)
    assert len(movies) > 0
    assert movies[0]["title"] in ["The Matrix", "Inception"]

def test_song_discovery():
    rag = RAGPipeline()
    rag.setup_sample_data()

    songs = rag.find_songs_by_time("night", top_k=2)
    assert len(songs) > 0
    assert any("night" in s["metadata"].get("best_time", "") for s in songs)

def test_intelligent_query():
    rag = RAGPipeline()
    rag.setup_sample_data()

    response = rag.query("What should I watch?", top_k=5)
    assert response
    assert len(response) > 10
```

## Performance Tips

1. **Reuse RAGPipeline Instance**
   ```python
   # Good
   rag = RAGPipeline()
   rag.setup_sample_data()
   movies = rag.find_movies_by_persona("tech_enthusiast")
   songs = rag.find_songs_by_time("night")

   # Avoid
   for persona in personas:
       rag = RAGPipeline()  # Don't recreate each time
   ```

2. **Use Caching**
   - Vector store caches results (L1 memory, L2 disk, L3 semantic)
   - Repeated queries are much faster

3. **Batch Operations**
   ```python
   # Efficient
   rag.setup_sample_data()  # Load once

   # Less efficient
   for i in range(100):
       rag.setup_sample_data()  # Don't reload
   ```

4. **Limit Results**
   ```python
   # Fast
   movies = rag.find_movies_by_persona("tech", top_k=5)

   # Slower
   movies = rag.find_movies_by_persona("tech", top_k=100)
   ```

## Troubleshooting

### No Results Returned

```python
# Check if data is loaded
health = rag.health_check()
print(health["collections"])

# If empty, load data
rag.setup_sample_data()

# Verify data exists
rag.vector_store.client.get_collection("movies")
```

### API Key Error

```python
# Set API key in environment
export ANTHROPIC_API_KEY=sk-ant-...

# Or pass to constructor
rag = RAGPipeline(api_key="sk-ant-...")
```

### Slow Queries

```python
# Check health
health = rag.health_check()

# Profile with logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Reduce top_k for faster results
movies = rag.find_movies_by_persona("tech", top_k=3)  # Faster
```

## Architecture

```
RAGPipeline
├── EmbeddingGenerator
│   └── SentenceTransformer (all-MiniLM-L6-v2)
├── VectorStore (ChromaDB)
│   ├── L1 Cache (Memory LRU)
│   ├── L2 Cache (Disk Persistent)
│   └── L3 Cache (Semantic Vector DB)
├── DocumentIngestionEngine
│   ├── Multi-format Parser
│   └── ThreadPool Processor
├── ClaudeRAGClient
│   └── Anthropic API
└── RAGQueryHandler
    └── Multi-source Search
```

## Best Practices

1. **Always Health Check on Startup**
   ```python
   rag = RAGPipeline()
   health = rag.health_check()
   if health["status"] != "healthy":
       raise RuntimeError("RAG system unhealthy")
   ```

2. **Use Context Collections Wisely**
   ```python
   # Specific
   response = rag.query(query, context_collections=["movies"], top_k=5)

   # Broad
   response = rag.query(query, top_k=20)
   ```

3. **Log All Queries for Analysis**
   - Enable structured logging
   - Track query patterns
   - Monitor performance

4. **Cache Embeddings**
   - RAG system automatically caches
   - Repeated queries are instant

---

**RAG Application powered by Claude, ChromaDB, and SentenceTransformers** 🚀
