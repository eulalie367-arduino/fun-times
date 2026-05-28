"""Example usage of the hybrid search module.

This demonstrates how to integrate the hybrid search layer into a RAG application.
"""

from src.vector_store import VectorStore
from src.embeddings import EmbeddingGenerator, MemoryEmbeddingCache, DiskEmbeddingCache
from src.retrieval.hybrid_search import HybridSearcher, BM25Indexer, CrossEncoderReranker
from src.config import get_settings


def example_basic_usage():
    """Basic usage example."""

    # Initialize settings
    settings = get_settings()

    # 1. Initialize embedding generator with caching
    cache_l1 = MemoryEmbeddingCache(max_size=1000, ttl=3600)
    cache_l2 = DiskEmbeddingCache(cache_dir="/data/cache", max_size_mb=500)

    embedding_gen = EmbeddingGenerator(
        model_name=settings.embedding_model,
        device="auto",
        batch_size=settings.embedding_batch_size,
        cache_l1=cache_l1,
        cache_l2=cache_l2
    )

    # 2. Initialize vector store
    vector_store = VectorStore(
        path=settings.chromadb_path,
        mode=settings.chromadb_mode
    )

    # Create collection
    vector_store.create_collection("documents")

    # 3. Initialize hybrid searcher
    bm25_indexer = BM25Indexer()
    reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-v2-m3")

    hybrid_searcher = HybridSearcher(
        vector_store=vector_store,
        embedding_generator=embedding_gen,
        collection_name="documents",
        bm25_indexer=bm25_indexer,
        reranker=reranker,
        rrf_k=60,
        rrf_alpha=0.5
    )

    # 4. Index documents
    documents = [
        {
            "id": "doc1",
            "content": "Machine learning is a subset of artificial intelligence focused on algorithms that learn from data.",
            "metadata": {"source": "wikipedia", "category": "AI"}
        },
        {
            "id": "doc2",
            "content": "Deep learning uses neural networks with multiple layers to process complex patterns in data.",
            "metadata": {"source": "arxiv", "category": "AI"}
        },
        {
            "id": "doc3",
            "content": "Natural language processing enables computers to understand and generate human language.",
            "metadata": {"source": "research_paper", "category": "NLP"}
        },
    ]

    # Index for hybrid search
    index_stats = hybrid_searcher.index_documents(documents)
    print(f"Indexed documents: {index_stats}")

    # Add to vector store
    embeddings = embedding_gen.embed_batch(
        [doc["content"] for doc in documents]
    )

    vector_store.add_vectors(
        collection_name="documents",
        documents=[doc["content"] for doc in documents],
        embeddings=[emb.tolist() for emb in embeddings],
        metadatas=[doc.get("metadata", {}) for doc in documents],
        ids=[doc["id"] for doc in documents]
    )

    # 5. Perform hybrid search
    query = "How does machine learning work?"

    results, stats = hybrid_searcher.search(
        query=query,
        top_k=5,
        use_cache=True,
        use_reranking=True,
        fuse_top_k=20
    )

    # Print results
    print(f"\nSearch Query: {query}")
    print(f"Execution Time: {stats.total_time_ms:.2f}ms")
    print(f"Cache Hit: {stats.cache_hit}")
    print(f"Results: {len(results)}")
    print()

    for i, result in enumerate(results, 1):
        print(f"{i}. [{result.source.upper()}] Score: {result.score:.4f}")
        print(f"   ID: {result.doc_id}")
        print(f"   Content: {result.content[:100]}...")
        print()

    # 6. Check cache statistics
    cache_stats = hybrid_searcher.get_cache_stats()
    print(f"Cache Statistics:")
    print(f"  Hit Rate: {cache_stats['hit_rate']}")
    print(f"  Size: {cache_stats['size']}/{cache_stats['max_size']}")

    # 7. Get overall statistics
    stats = hybrid_searcher.get_stats()
    print(f"\nHybrid Search Configuration:")
    print(f"  RRF K: {stats['rrf_config']['k']}")
    print(f"  RRF Alpha (weighting): {stats['rrf_config']['alpha']}")


def example_performance_testing():
    """Example of performance testing and benchmarking."""

    import time

    settings = get_settings()

    # Setup components
    embedding_gen = EmbeddingGenerator(
        model_name=settings.embedding_model,
        device="auto"
    )

    vector_store = VectorStore(path=settings.chromadb_path)
    vector_store.create_collection("perf_test")

    hybrid_searcher = HybridSearcher(
        vector_store=vector_store,
        embedding_generator=embedding_gen,
        collection_name="perf_test"
    )

    # Generate test documents
    test_docs = [
        {
            "id": f"doc{i}",
            "content": f"Document {i} about machine learning and AI topics number {i}"
        }
        for i in range(100)
    ]

    hybrid_searcher.index_documents(test_docs)

    # Add to vector store
    embeddings = embedding_gen.embed_batch(
        [doc["content"] for doc in test_docs]
    )

    vector_store.add_vectors(
        collection_name="perf_test",
        documents=[doc["content"] for doc in test_docs],
        embeddings=[emb.tolist() for emb in embeddings],
        ids=[doc["id"] for doc in test_docs]
    )

    # Run performance tests
    test_queries = [
        "machine learning",
        "artificial intelligence",
        "neural networks",
        "deep learning"
    ]

    print("\nPerformance Test Results:")
    print("=" * 60)

    total_time = 0
    cache_hits = 0

    for i, query in enumerate(test_queries * 2):  # Run twice to test cache
        start = time.time()
        results, stats = hybrid_searcher.search(query, top_k=5)
        duration = (time.time() - start) * 1000

        total_time += duration
        if stats.cache_hit:
            cache_hits += 1

        print(f"Query {i+1}: '{query}'")
        print(f"  Time: {duration:.2f}ms")
        print(f"  Cache Hit: {stats.cache_hit}")
        print(f"  Results: {stats.final_results}")
        print()

    # Summary
    print("=" * 60)
    avg_time = total_time / len(test_queries * 2)
    cache_hit_rate = (cache_hits / (len(test_queries * 2))) * 100

    print(f"Average Query Time: {avg_time:.2f}ms")
    print(f"Cache Hit Rate: {cache_hit_rate:.1f}%")
    print(f"Target Hit Rate: 60-80%")


def example_custom_configuration():
    """Example with custom configuration."""

    settings = get_settings()

    embedding_gen = EmbeddingGenerator(
        model_name=settings.embedding_model,
        device="auto"
    )

    vector_store = VectorStore(path=settings.chromadb_path)
    vector_store.create_collection("custom_config")

    # Custom RRF parameters
    hybrid_searcher = HybridSearcher(
        vector_store=vector_store,
        embedding_generator=embedding_gen,
        collection_name="custom_config",
        rrf_k=100,  # Different RRF parameter
        rrf_alpha=0.7  # Favor BM25 (sparse) over dense
    )

    # Index documents
    documents = [
        {
            "id": "d1",
            "content": "Hybrid search combines multiple retrieval methods"
        },
        {
            "id": "d2",
            "content": "BM25 provides efficient keyword-based matching"
        }
    ]

    hybrid_searcher.index_documents(documents)

    # Search with custom parameters
    results, stats = hybrid_searcher.search(
        query="hybrid search methods",
        top_k=10,
        use_cache=False,  # Disable cache for this query
        use_reranking=False,  # Disable reranking for speed
        fuse_top_k=15
    )

    print("Custom Configuration Results:")
    print(f"Alpha (sparse weight): {hybrid_searcher.rrf_alpha}")
    print(f"RRF K: {hybrid_searcher.rrf_k}")
    print(f"Results: {len(results)}")

    for result in results[:3]:
        print(f"- {result.doc_id}: {result.content[:60]}...")


if __name__ == "__main__":
    print("Hybrid Search Examples\n")

    # Run basic usage
    print("1. Basic Usage Example")
    print("-" * 60)
    # example_basic_usage()  # Uncomment to run

    # Run performance testing
    print("\n2. Performance Testing")
    print("-" * 60)
    # example_performance_testing()  # Uncomment to run

    # Run custom configuration
    print("\n3. Custom Configuration")
    print("-" * 60)
    # example_custom_configuration()  # Uncomment to run

    print("\nNote: Uncomment examples in __main__ to run")
