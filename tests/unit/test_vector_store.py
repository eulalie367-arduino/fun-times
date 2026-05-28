"""Tests for vector store integration."""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.vector_store import VectorStore, ChromaDBClient
from src.exceptions import VectorStoreError


class TestVectorStore:
    """Test VectorStore class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for ChromaDB."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create VectorStore instance."""
        return VectorStore(
            path=temp_dir,
            mode="persistent",
            timeout=30
        )

    def test_vector_store_initialization(self, vector_store):
        """Test VectorStore initializes correctly."""
        assert vector_store is not None
        assert vector_store.path is not None

    def test_create_collection(self, vector_store):
        """Test creating a collection."""
        collection = vector_store.create_collection(
            name="test_collection",
            metadata={"type": "test"}
        )
        assert collection is not None
        assert collection.name == "test_collection"

    def test_add_vectors(self, vector_store):
        """Test adding vectors to collection."""
        vector_store.create_collection("test_collection")

        documents = ["Hello world", "This is a test"]
        embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        metadatas = [
            {"source": "doc1"},
            {"source": "doc2"}
        ]
        ids = ["id1", "id2"]

        result = vector_store.add_vectors(
            collection_name="test_collection",
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        assert result is not None

    def test_search(self, vector_store):
        """Test searching vectors."""
        vector_store.create_collection("test_collection")

        # Add vectors
        documents = ["Hello world", "This is a test"]
        embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        vector_store.add_vectors(
            collection_name="test_collection",
            documents=documents,
            embeddings=embeddings,
            metadatas=[{"source": "doc1"}, {"source": "doc2"}],
            ids=["id1", "id2"]
        )

        # Search
        query_embedding = [0.1, 0.2, 0.3]
        results = vector_store.search(
            collection_name="test_collection",
            query_embeddings=[query_embedding],
            n_results=2
        )
        assert results is not None
        assert len(results["documents"]) > 0

    def test_delete_vectors(self, vector_store):
        """Test deleting vectors."""
        vector_store.create_collection("test_collection")

        # Add vectors
        vector_store.add_vectors(
            collection_name="test_collection",
            documents=["Test"],
            embeddings=[[0.1, 0.2, 0.3]],
            metadatas=[{"source": "doc1"}],
            ids=["id1"]
        )

        # Delete
        result = vector_store.delete(
            collection_name="test_collection",
            ids=["id1"]
        )
        assert result is not None

    def test_collection_count(self, vector_store):
        """Test getting collection count."""
        vector_store.create_collection("test_collection")

        vector_store.add_vectors(
            collection_name="test_collection",
            documents=["Doc1", "Doc2"],
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            metadatas=[{"source": "doc1"}, {"source": "doc2"}],
            ids=["id1", "id2"]
        )

        count = vector_store.count(collection_name="test_collection")
        assert count == 2

    def test_list_collections(self, vector_store):
        """Test listing collections."""
        vector_store.create_collection("collection1")
        vector_store.create_collection("collection2")

        collections = vector_store.list_collections()
        assert len(collections) >= 2

    def test_delete_collection(self, vector_store):
        """Test deleting a collection."""
        vector_store.create_collection("to_delete")
        vector_store.delete_collection("to_delete")

        collections = vector_store.list_collections()
        assert "to_delete" not in [c.name for c in collections]

    def test_metadata_filtering(self, vector_store):
        """Test metadata filtering in search."""
        vector_store.create_collection("test_collection")

        vector_store.add_vectors(
            collection_name="test_collection",
            documents=["Doc1", "Doc2"],
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            metadatas=[
                {"source": "file1", "type": "text"},
                {"source": "file2", "type": "code"}
            ],
            ids=["id1", "id2"]
        )

        # Search with metadata filter
        results = vector_store.search(
            collection_name="test_collection",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=2,
            where={"type": "text"}
        )
        assert results is not None

    def test_health_check(self, vector_store):
        """Test health check."""
        health = vector_store.health_check()
        assert health["status"] == "healthy"
        assert "components" in health

    def test_get_stats(self, vector_store):
        """Test getting statistics."""
        vector_store.create_collection("test_collection")

        stats = vector_store.get_stats()
        assert stats is not None
        assert "collections" in stats


class TestChromatDBClient:
    """Test ChromaDBClient class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def client(self, temp_dir):
        """Create ChromaDB client."""
        return ChromaDBClient(
            path=temp_dir,
            mode="persistent",
            timeout=30
        )

    def test_client_initialization(self, client):
        """Test client initializes."""
        assert client is not None

    def test_get_or_create_client(self, client):
        """Test get_or_create_client."""
        chroma_client = client.get_or_create_client()
        assert chroma_client is not None

    def test_client_health_check(self, client):
        """Test client health check."""
        health = client.health_check()
        assert health is not None

    def test_client_error_handling(self):
        """Test error handling."""
        # Try to connect to invalid host
        client = ChromaDBClient(
            host="invalid-host",
            port=9999,
            timeout=1
        )
        # Should not raise during init, but during operation
        assert client is not None


class TestVectorStoreErrorHandling:
    """Test error handling in VectorStore."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create VectorStore instance."""
        return VectorStore(path=temp_dir, mode="persistent")

    def test_invalid_collection_name(self, vector_store):
        """Test accessing non-existent collection."""
        with pytest.raises(Exception):
            vector_store.count(collection_name="nonexistent")

    def test_invalid_embedding_dimension(self, vector_store):
        """Test mismatched embedding dimensions."""
        vector_store.create_collection("test")

        with pytest.raises(Exception):
            vector_store.add_vectors(
                collection_name="test",
                documents=["doc"],
                embeddings=[[0.1, 0.2]],  # Wrong dimension
                metadatas=[{"source": "doc"}],
                ids=["id1"]
            )

    def test_empty_results(self, vector_store):
        """Test searching empty collection."""
        vector_store.create_collection("test")

        results = vector_store.search(
            collection_name="test",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=5
        )
        assert results["documents"] == [[]]


class TestQueryCaching:
    """Test query result caching."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create VectorStore instance."""
        return VectorStore(path=temp_dir, mode="persistent")

    def test_cache_hit(self, vector_store):
        """Test cache hit scenario."""
        vector_store.create_collection("test")
        vector_store.add_vectors(
            collection_name="test",
            documents=["Test doc"],
            embeddings=[[0.1, 0.2, 0.3]],
            metadatas=[{"source": "test"}],
            ids=["id1"]
        )

        # First search
        query = [[0.1, 0.2, 0.3]]
        result1 = vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=query,
            n_results=5,
            use_cache=True
        )

        # Second search - should hit cache
        result2 = vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=query,
            n_results=5,
            use_cache=True
        )

        stats = vector_store.get_cache_stats()
        assert stats["hits"] >= 1

    def test_cache_disabled(self, vector_store):
        """Test cache can be disabled."""
        vector_store.create_collection("test")
        vector_store.add_vectors(
            collection_name="test",
            documents=["Test"],
            embeddings=[[0.1, 0.2, 0.3]],
            metadatas=[{"source": "test"}],
            ids=["id1"]
        )

        result1 = vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=5,
            use_cache=False
        )
        assert result1 is not None

    def test_cache_statistics(self, vector_store):
        """Test cache statistics."""
        stats = vector_store.get_cache_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert stats["type"] == "query"


class TestSemanticChunking:
    """Test semantic text chunking."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create VectorStore instance."""
        return VectorStore(path=temp_dir, mode="persistent")

    def test_basic_chunking(self, vector_store):
        """Test basic semantic chunking."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = vector_store.chunk_text_semantically(
            text=text,
            chunk_size=20,
            overlap=5
        )

        assert len(chunks) > 0
        for chunk_text, start_pos, end_pos in chunks:
            assert isinstance(chunk_text, str)
            assert isinstance(start_pos, int)
            assert isinstance(end_pos, int)
            assert start_pos >= 0
            assert end_pos > start_pos

    def test_position_tracking(self, vector_store):
        """Test that positions are tracked correctly."""
        text = "First. Second. Third."
        chunks = vector_store.chunk_text_semantically(
            text=text,
            chunk_size=50,
            overlap=0
        )

        assert len(chunks) > 0
        # Verify chunks don't overlap with no overlap setting
        for i in range(len(chunks) - 1):
            _, _, end_pos1 = chunks[i]
            _, start_pos2, _ = chunks[i + 1]
            # Positions should be sequential (allowing for whitespace)
            assert start_pos2 >= end_pos1 - 1

    def test_overlap_handling(self, vector_store):
        """Test overlap handling in chunking."""
        text = "Sentence one. Sentence two. Sentence three. Sentence four."
        chunks = vector_store.chunk_text_semantically(
            text=text,
            chunk_size=20,
            overlap=5
        )

        assert len(chunks) > 0


class TestCacheManagement:
    """Test cache management methods."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create VectorStore instance."""
        return VectorStore(path=temp_dir, mode="persistent")

    def test_clear_cache(self, vector_store):
        """Test clearing cache."""
        vector_store.create_collection("test")
        vector_store.add_vectors(
            collection_name="test",
            documents=["Test"],
            embeddings=[[0.1, 0.2, 0.3]],
            metadatas=[{"source": "test"}],
            ids=["id1"]
        )

        # Populate cache
        vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=5
        )

        # Clear and verify
        vector_store.clear_cache()
        stats = vector_store.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0

    def test_invalidate_metadata_cache(self, vector_store):
        """Test metadata cache invalidation."""
        vector_store.create_collection("test")
        vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=5
        )

        # Invalidate
        vector_store.invalidate_metadata_cache()
        stats = vector_store.get_cache_stats()
        assert stats["size"] == 0

    def test_cache_stats_reporting(self, vector_store):
        """Test comprehensive cache statistics."""
        vector_store.create_collection("test")
        vector_store.add_vectors(
            collection_name="test",
            documents=["Doc1", "Doc2"],
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            metadatas=[{"source": "doc1"}, {"source": "doc2"}],
            ids=["id1", "id2"]
        )

        # Perform some searches
        vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=5
        )
        vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=5
        )

        stats = vector_store.get_cache_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "size" in stats
        assert "ttl" in stats
        assert "type" in stats and stats["type"] == "query"
