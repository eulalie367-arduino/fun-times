"""Vector store integration with ChromaDB."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any, Tuple
from src.logger import get_logger
from src.exceptions import VectorStoreError
from src.retry import with_retry
import time
import re
from src.embeddings import MemoryEmbeddingCache


logger = get_logger(__name__)


class ChromaDBClient:
    """ChromaDB client wrapper with connection management."""

    def __init__(
        self,
        path: str = "/data/chroma",
        host: Optional[str] = None,
        port: Optional[int] = None,
        mode: str = "persistent",
        timeout: int = 30
    ):
        """Initialize ChromaDB client."""
        self.path = path
        self.host = host
        self.port = port
        self.mode = mode
        self.timeout = timeout
        self._client = None

        logger.msg(
            "chromadb_client_init",
            mode=mode,
            path=path if mode == "persistent" else None,
            host=host,
            port=port
        )

    @with_retry(max_attempts=3, initial_wait=1)
    def get_or_create_client(self):
        """Get or create ChromaDB client with retry."""
        if self._client is not None:
            return self._client

        try:
            if self.mode == "persistent":
                settings = Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.path,
                    anonymized_telemetry=False,
                    allow_reset=True
                )
                self._client = chromadb.Client(settings)
            elif self.mode == "memory":
                self._client = chromadb.Client()
            else:
                raise VectorStoreError(f"Unknown mode: {self.mode}")

            logger.msg("chromadb_client_created", mode=self.mode)
            return self._client

        except Exception as e:
            logger.msg(
                "chromadb_client_error",
                error=str(e),
                mode=self.mode
            )
            raise VectorStoreError(f"Failed to create ChromaDB client: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Check client health."""
        try:
            client = self.get_or_create_client()
            # Try to get heartbeat
            client.get_or_create_collection("_health_check")
            client.delete_collection("_health_check")

            logger.msg("chromadb_health_check", status="healthy")
            return {"status": "healthy"}
        except Exception as e:
            logger.msg("chromadb_health_check", status="unhealthy", error=str(e))
            return {"status": "unhealthy", "error": str(e)}

    def reset(self):
        """Reset the client."""
        try:
            client = self.get_or_create_client()
            client.reset()
            self._client = None
            logger.msg("chromadb_reset_complete")
        except Exception as e:
            logger.msg("chromadb_reset_error", error=str(e))
            raise VectorStoreError(f"Failed to reset client: {e}")


class VectorStore:
    """Vector store wrapper for ChromaDB with CRUD operations."""

    def __init__(
        self,
        path: str = "/data/chroma",
        host: Optional[str] = None,
        port: Optional[int] = None,
        mode: str = "persistent",
        timeout: int = 30
    ):
        """Initialize VectorStore."""
        self.path = path
        self.host = host
        self.port = port
        self.mode = mode
        self.timeout = timeout
        self.client = ChromaDBClient(
            path=path,
            host=host,
            port=port,
            mode=mode,
            timeout=timeout
        )
        self._chroma = None
        self._query_cache = {}
        self._cache_ttl = 3600
        self._search_with_cache_hits = 0
        self._search_with_cache_misses = 0

        logger.msg(
            "vector_store_init",
            mode=mode,
            path=path if mode == "persistent" else None
        )

    @property
    def chroma(self):
        """Get or create ChromaDB client."""
        if self._chroma is None:
            self._chroma = self.client.get_or_create_client()
        return self._chroma

    def create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create a new collection."""
        try:
            collection = self.chroma.get_or_create_collection(
                name=name,
                metadata=metadata or {}
            )
            logger.msg("collection_created", name=name, metadata=metadata)
            return collection
        except Exception as e:
            logger.msg("collection_creation_error", name=name, error=str(e))
            raise VectorStoreError(f"Failed to create collection {name}: {e}")

    def delete_collection(self, name: str):
        """Delete a collection."""
        try:
            self.chroma.delete_collection(name=name)
            logger.msg("collection_deleted", name=name)
        except Exception as e:
            logger.msg("collection_deletion_error", name=name, error=str(e))
            raise VectorStoreError(f"Failed to delete collection {name}: {e}")

    def list_collections(self):
        """List all collections."""
        try:
            collections = self.chroma.list_collections()
            logger.msg("collections_listed", count=len(collections))
            return collections
        except Exception as e:
            logger.msg("collections_list_error", error=str(e))
            raise VectorStoreError(f"Failed to list collections: {e}")

    def add_vectors(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add vectors to collection."""
        try:
            if not ids:
                ids = [f"id_{i}_{int(time.time() * 1000)}" for i in range(len(documents))]

            collection = self.chroma.get_collection(name=collection_name)
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas or [{}] * len(documents),
                ids=ids
            )

            logger.msg(
                "vectors_added",
                collection=collection_name,
                count=len(documents)
            )
            return {"status": "success", "ids": ids}

        except Exception as e:
            logger.msg(
                "vectors_add_error",
                collection=collection_name,
                error=str(e)
            )
            raise VectorStoreError(f"Failed to add vectors: {e}")

    def search(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ):
        """Search for similar vectors."""
        try:
            collection = self.chroma.get_collection(name=collection_name)

            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )

            logger.msg(
                "vectors_searched",
                collection=collection_name,
                n_results=n_results,
                results_found=len(results["documents"][0]) if results["documents"] else 0
            )
            return results

        except Exception as e:
            logger.msg(
                "vectors_search_error",
                collection=collection_name,
                error=str(e)
            )
            raise VectorStoreError(f"Failed to search vectors: {e}")

    def search_with_cache(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ):
        """Search with query result caching."""
        try:
            cache_key = f"{collection_name}:{str(query_embeddings)[:100]}:{n_results}:{str(where)}"

            if use_cache and cache_key in self._query_cache:
                cached_results, timestamp = self._query_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    self._search_with_cache_hits += 1
                    logger.msg("query_cache_hit", cache_key=cache_key)
                    return cached_results

            results = self.search(collection_name, query_embeddings, n_results, where)
            self._query_cache[cache_key] = (results, time.time())
            self._search_with_cache_misses += 1

            logger.msg(
                "query_cache_miss",
                collection=collection_name,
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.msg(
                "search_with_cache_error",
                collection=collection_name,
                error=str(e)
            )
            raise VectorStoreError(f"Failed to search with cache: {e}")

    def chunk_text_semantically(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 100,
        embedding_fn=None
    ) -> List[Tuple[str, int, int]]:
        """Chunk text by semantic boundaries (sentences)."""
        try:
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            chunks = []
            current_chunk = ""
            start_pos = 0

            for sentence in sentences:
                # Check if adding sentence would exceed chunk_size
                test_chunk = current_chunk + " " + sentence if current_chunk else sentence

                if len(test_chunk) > chunk_size and current_chunk:
                    # Save current chunk
                    end_pos = start_pos + len(current_chunk)
                    chunks.append((current_chunk.strip(), start_pos, end_pos))

                    # Start new chunk with overlap
                    overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                    current_chunk = overlap_text + " " + sentence
                    start_pos = max(0, end_pos - overlap)
                else:
                    current_chunk = test_chunk

            # Add final chunk
            if current_chunk:
                end_pos = start_pos + len(current_chunk)
                chunks.append((current_chunk.strip(), start_pos, end_pos))

            logger.msg(
                "text_chunked_semantically",
                text_length=len(text),
                num_chunks=len(chunks)
            )
            return chunks

        except Exception as e:
            logger.msg(
                "semantic_chunking_error",
                error=str(e)
            )
            raise VectorStoreError(f"Failed to chunk text semantically: {e}")

    def update(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """Update vectors in collection."""
        try:
            collection = self.chroma.get_collection(name=collection_name)

            update_kwargs = {"ids": ids}
            if documents:
                update_kwargs["documents"] = documents
            if embeddings:
                update_kwargs["embeddings"] = embeddings
            if metadatas:
                update_kwargs["metadatas"] = metadatas

            collection.update(**update_kwargs)

            logger.msg(
                "vectors_updated",
                collection=collection_name,
                count=len(ids)
            )
            return {"status": "success"}

        except Exception as e:
            logger.msg(
                "vectors_update_error",
                collection=collection_name,
                error=str(e)
            )
            raise VectorStoreError(f"Failed to update vectors: {e}")

    def delete(
        self,
        collection_name: str,
        ids: List[str]
    ):
        """Delete vectors from collection."""
        try:
            collection = self.chroma.get_collection(name=collection_name)
            collection.delete(ids=ids)

            logger.msg(
                "vectors_deleted",
                collection=collection_name,
                count=len(ids)
            )
            return {"status": "success"}

        except Exception as e:
            logger.msg(
                "vectors_delete_error",
                collection=collection_name,
                error=str(e)
            )
            raise VectorStoreError(f"Failed to delete vectors: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get query cache statistics."""
        total = self._search_with_cache_hits + self._search_with_cache_misses
        hit_rate = (
            self._search_with_cache_hits / total * 100
        ) if total > 0 else 0

        return {
            "type": "query",
            "hits": self._search_with_cache_hits,
            "misses": self._search_with_cache_misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self._query_cache),
            "ttl": self._cache_ttl
        }

    def clear_cache(self) -> None:
        """Clear query result cache."""
        self._query_cache.clear()
        self._search_with_cache_hits = 0
        self._search_with_cache_misses = 0
        logger.msg("query_cache_cleared")

    def invalidate_metadata_cache(self) -> None:
        """Invalidate cache after metadata updates."""
        self.clear_cache()
        logger.msg("metadata_cache_invalidated")

    def count(self, collection_name: str) -> int:
        """Get document count in collection."""
        try:
            collection = self.chroma.get_collection(name=collection_name)
            count = collection.count()

            logger.msg("collection_count", collection=collection_name, count=count)
            return count

        except Exception as e:
            logger.msg(
                "collection_count_error",
                collection=collection_name,
                error=str(e)
            )
            raise VectorStoreError(f"Failed to get collection count: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on vector store."""
        health = {
            "status": "healthy",
            "components": {}
        }

        try:
            # Check ChromaDB
            chroma_health = self.client.health_check()
            health["components"]["chromadb"] = chroma_health.get("status", "unknown")

            # Check collections access
            try:
                self.list_collections()
                health["components"]["collections"] = "ok"
            except Exception as e:
                health["components"]["collections"] = f"error: {str(e)}"
                health["status"] = "unhealthy"

        except Exception as e:
            health["status"] = "unhealthy"
            health["components"]["chromadb"] = f"error: {str(e)}"

        logger.msg("vector_store_health_check", result=health)
        return health

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            collections = self.list_collections()
            stats = {
                "collections": len(collections),
                "collection_details": []
            }

            for collection in collections:
                try:
                    count = collection.count()
                    stats["collection_details"].append({
                        "name": collection.name,
                        "count": count,
                        "metadata": collection.metadata
                    })
                except Exception as e:
                    logger.msg(
                        "collection_stats_error",
                        collection=collection.name,
                        error=str(e)
                    )

            logger.msg("vector_store_stats", stats=stats)
            return stats

        except Exception as e:
            logger.msg("vector_store_stats_error", error=str(e))
            raise VectorStoreError(f"Failed to get stats: {e}")
