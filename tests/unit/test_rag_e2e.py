"""End-to-end RAG tests for complete pipeline functionality."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.embeddings import EmbeddingGenerator
from src.vector_store import VectorStore
from src.llm_integration import ClaudeRAGClient, RAGQueryHandler
from src.ingestion.engine import DocumentIngestionEngine
from src.logger import get_logger


logger = get_logger(__name__)


class TestRAGEndToEnd:
    """End-to-end tests for the complete RAG pipeline."""

    @pytest.fixture
    def embedding_generator(self):
        """Create embedding generator."""
        return EmbeddingGenerator(model_name="all-MiniLM-L6-v2")

    @pytest.fixture
    def vector_store(self, tmp_path):
        """Create vector store with persistence."""
        db_path = tmp_path / "chroma_db"
        store = VectorStore(persist_dir=str(db_path))
        yield store
        store.client.delete_collection(name="movies")
        store.client.delete_collection(name="songs")
        store.client.delete_collection(name="documents")

    @pytest.fixture
    def sample_movies_data(self):
        """Load sample movies data."""
        with open("data/movies.json") as f:
            return json.load(f)

    @pytest.fixture
    def sample_songs_data(self):
        """Load sample songs data."""
        with open("data/songs.json") as f:
            return json.load(f)

    @pytest.fixture
    def llm_client(self):
        """Create mocked LLM client."""
        return ClaudeRAGClient(api_key="test-key")

    @pytest.fixture
    def query_handler(self, vector_store, embedding_generator, llm_client):
        """Create RAG query handler."""
        return RAGQueryHandler(vector_store, embedding_generator, llm_client)

    def test_ingest_movies_into_vector_store(
        self, vector_store, embedding_generator, sample_movies_data
    ):
        """Test ingesting movie data into vector store."""
        movies = sample_movies_data["movies"]

        # Prepare documents and embeddings
        documents = [
            f"{m['title']} - {m['description']}"
            for m in movies
        ]
        embeddings = embedding_generator.embed_texts(documents)

        # Add to collection
        vector_store.add(
            collection_name="movies",
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                {
                    "title": m["title"],
                    "genre": ",".join(m["genre"]),
                    "personas": ",".join(m["personas"]),
                    "year": m["year"],
                    "rating": m["rating"]
                }
                for m in movies
            ],
            ids=[m["id"] for m in movies]
        )

        # Verify collection was created
        assert vector_store.client.get_collection(name="movies") is not None
        logger.msg("movies_ingested", count=len(movies))

    def test_ingest_songs_into_vector_store(
        self, vector_store, embedding_generator, sample_songs_data
    ):
        """Test ingesting song data into vector store."""
        songs = sample_songs_data["songs"]

        # Prepare documents and embeddings
        documents = [
            f"{s['title']} by {s['artist']} - {s['description']}"
            for s in songs
        ]
        embeddings = embedding_generator.embed_texts(documents)

        # Add to collection
        vector_store.add(
            collection_name="songs",
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                {
                    "title": s["title"],
                    "artist": s["artist"],
                    "genre": ",".join(s["genre"]),
                    "mood": ",".join(s["mood"]),
                    "best_time": ",".join(s["best_time"]),
                    "year": s["year"]
                }
                for s in songs
            ],
            ids=[s["id"] for s in songs]
        )

        # Verify collection was created
        assert vector_store.client.get_collection(name="songs") is not None
        logger.msg("songs_ingested", count=len(songs))

    def test_find_movie_by_persona_tech_enthusiast(
        self, vector_store, embedding_generator, sample_movies_data
    ):
        """Test finding movies for tech_enthusiast persona."""
        movies = sample_movies_data["movies"]

        # Ingest movies
        documents = [
            f"{m['title']} - {m['description']}"
            for m in movies
        ]
        embeddings = embedding_generator.embed_texts(documents)
        vector_store.add(
            collection_name="movies",
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                {
                    "title": m["title"],
                    "personas": ",".join(m["personas"]),
                }
                for m in movies
            ],
            ids=[m["id"] for m in movies]
        )

        # Search for tech_enthusiast movies
        persona_embedding = embedding_generator.embed_text("tech_enthusiast")
        results = vector_store.search(
            collection_name="movies",
            query_embeddings=[persona_embedding],
            n_results=3
        )

        # Should find Matrix and Inception (high tech relevance)
        assert len(results["ids"][0]) >= 1
        titles = results["documents"][0]
        assert any("Matrix" in t for t in titles)
        logger.msg("tech_persona_search_success", results=len(titles))

    def test_find_movie_by_persona_drama_lover(
        self, vector_store, embedding_generator, sample_movies_data
    ):
        """Test finding movies for drama_lover persona."""
        movies = sample_movies_data["movies"]

        # Ingest movies
        documents = [
            f"{m['title']} - {m['description']}"
            for m in movies
        ]
        embeddings = embedding_generator.embed_texts(documents)
        vector_store.add(
            collection_name="movies",
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                {
                    "title": m["title"],
                    "personas": ",".join(m["personas"]),
                }
                for m in movies
            ],
            ids=[m["id"] for m in movies]
        )

        # Search for drama_lover movies
        persona_embedding = embedding_generator.embed_text("drama_lover emotional")
        results = vector_store.search(
            collection_name="movies",
            query_embeddings=[persona_embedding],
            n_results=3
        )

        # Should find Shawshank Redemption
        assert len(results["ids"][0]) >= 1
        titles = results["documents"][0]
        assert any("Shawshank" in t or "Pulp" in t for t in titles)
        logger.msg("drama_persona_search_success", results=len(titles))

    def test_find_song_by_time_morning(
        self, vector_store, embedding_generator, sample_songs_data
    ):
        """Test finding songs suitable for morning."""
        songs = sample_songs_data["songs"]

        # Ingest songs
        documents = [
            f"{s['title']} by {s['artist']} - {s['description']}"
            for s in songs
        ]
        embeddings = embedding_generator.embed_texts(documents)
        vector_store.add(
            collection_name="songs",
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                {
                    "title": s["title"],
                    "best_time": ",".join(s["best_time"]),
                }
                for s in songs
            ],
            ids=[s["id"] for s in songs]
        )

        # Search for morning songs
        morning_embedding = embedding_generator.embed_text("songs for morning calm peaceful")
        results = vector_store.search(
            collection_name="songs",
            query_embeddings=[morning_embedding],
            n_results=2
        )

        # Should find Clair de Lune (morning suitable)
        assert len(results["ids"][0]) >= 1
        titles = results["documents"][0]
        assert any("Clair" in t for t in titles)
        logger.msg("morning_song_search_success", results=len(titles))

    def test_find_song_by_time_night(
        self, vector_store, embedding_generator, sample_songs_data
    ):
        """Test finding songs suitable for night."""
        songs = sample_songs_data["songs"]

        # Ingest songs
        documents = [
            f"{s['title']} by {s['artist']} - {s['description']}"
            for s in songs
        ]
        embeddings = embedding_generator.embed_texts(documents)
        vector_store.add(
            collection_name="songs",
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                {
                    "title": s["title"],
                    "best_time": ",".join(s["best_time"]),
                }
                for s in songs
            ],
            ids=[s["id"] for s in songs]
        )

        # Search for night songs
        night_embedding = embedding_generator.embed_text("songs for night party energetic")
        results = vector_store.search(
            collection_name="songs",
            query_embeddings=[night_embedding],
            n_results=2
        )

        # Should find Midnight City or Bohemian Rhapsody (night suitable)
        assert len(results["ids"][0]) >= 1
        titles = results["documents"][0]
        assert any("Midnight" in t or "Bohemian" in t for t in titles)
        logger.msg("night_song_search_success", results=len(titles))

    def test_rag_query_handler_movie_persona(
        self, query_handler, vector_store, embedding_generator, sample_movies_data
    ):
        """Test RAGQueryHandler movie persona matching."""
        movies = sample_movies_data["movies"]

        # Ingest movies
        documents = [
            f"{m['title']} - {m['description']}"
            for m in movies
        ]
        embeddings = embedding_generator.embed_texts(documents)
        vector_store.add(
            collection_name="movies",
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                {
                    "title": m["title"],
                    "personas": ",".join(m["personas"]),
                }
                for m in movies
            ],
            ids=[m["id"] for m in movies]
        )

        # Use handler to find movies
        results = query_handler.find_movie_by_persona("tech_enthusiast", top_k=3)

        assert results["ids"]
        assert results["documents"]
        logger.msg("handler_movie_search_success")

    def test_rag_query_handler_song_time(
        self, query_handler, vector_store, embedding_generator, sample_songs_data
    ):
        """Test RAGQueryHandler song time matching."""
        songs = sample_songs_data["songs"]

        # Ingest songs
        documents = [
            f"{s['title']} by {s['artist']} - {s['description']}"
            for s in songs
        ]
        embeddings = embedding_generator.embed_texts(documents)
        vector_store.add(
            collection_name="songs",
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                {
                    "title": s["title"],
                    "best_time": ",".join(s["best_time"]),
                }
                for s in songs
            ],
            ids=[s["id"] for s in songs]
        )

        # Use handler to find songs
        results = query_handler.find_song_by_time("night", mood="energetic", top_k=2)

        assert results["ids"]
        assert results["documents"]
        logger.msg("handler_song_search_success")

    @patch('src.llm_integration.anthropic')
    def test_intelligent_query_with_context(
        self, mock_anthropic, query_handler, vector_store, embedding_generator,
        sample_movies_data, sample_songs_data
    ):
        """Test intelligent query with multi-source context."""
        # Mock Claude API
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Recommended: The Matrix for tech enthusiasts")]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.Anthropic.return_value = mock_client

        # Ingest movies and songs
        movies = sample_movies_data["movies"]
        songs = sample_songs_data["songs"]

        movie_docs = [f"{m['title']} - {m['description']}" for m in movies]
        movie_embeddings = embedding_generator.embed_texts(movie_docs)
        vector_store.add(
            collection_name="movies",
            documents=movie_docs,
            embeddings=movie_embeddings,
            metadatas=[{"title": m["title"]} for m in movies],
            ids=[m["id"] for m in movies]
        )

        song_docs = [f"{s['title']} by {s['artist']}" for s in songs]
        song_embeddings = embedding_generator.embed_texts(song_docs)
        vector_store.add(
            collection_name="songs",
            documents=song_docs,
            embeddings=song_embeddings,
            metadatas=[{"title": s["title"]} for s in songs],
            ids=[s["id"] for s in songs]
        )

        # Execute intelligent query
        response = query_handler.intelligent_query(
            query="What movie should a tech enthusiast watch tonight?",
            context_docs=[],
            top_k=2
        )

        assert response
        assert "Matrix" in response or "Recommended" in response
        logger.msg("intelligent_query_success")

    def test_complete_rag_workflow(
        self, vector_store, embedding_generator, query_handler,
        sample_movies_data, sample_songs_data
    ):
        """Test complete RAG workflow with all components."""
        # Step 1: Ingest all data
        movies = sample_movies_data["movies"]
        songs = sample_songs_data["songs"]

        # Ingest movies
        movie_docs = [f"{m['title']} - {m['description']}" for m in movies]
        movie_embeddings = embedding_generator.embed_texts(movie_docs)
        vector_store.add(
            collection_name="movies",
            documents=movie_docs,
            embeddings=movie_embeddings,
            metadatas=[
                {
                    "title": m["title"],
                    "personas": ",".join(m["personas"]),
                    "rating": m["rating"]
                }
                for m in movies
            ],
            ids=[m["id"] for m in movies]
        )

        # Ingest songs
        song_docs = [f"{s['title']} by {s['artist']}" for s in songs]
        song_embeddings = embedding_generator.embed_texts(song_docs)
        vector_store.add(
            collection_name="songs",
            documents=song_docs,
            embeddings=song_embeddings,
            metadatas=[
                {
                    "title": s["title"],
                    "best_time": ",".join(s["best_time"]),
                    "mood": ",".join(s["mood"])
                }
                for s in songs
            ],
            ids=[s["id"] for s in songs]
        )

        # Step 2: Query movies by persona
        movies_result = query_handler.find_movie_by_persona("sci-fi fan", top_k=2)
        assert movies_result["ids"]

        # Step 3: Query songs by time
        songs_result = query_handler.find_song_by_time("night", top_k=2)
        assert songs_result["ids"]

        logger.msg("complete_workflow_success", movies=len(movies_result["ids"][0]), songs=len(songs_result["ids"][0]))


class TestRAGWithDocuments:
    """Test RAG with real document ingestion."""

    @pytest.fixture
    def ingestion_engine(self, tmp_path):
        """Create document ingestion engine."""
        return DocumentIngestionEngine(
            num_workers=2,
            batch_size=5
        )

    @pytest.fixture
    def embedding_generator(self):
        """Create embedding generator."""
        return EmbeddingGenerator(model_name="all-MiniLM-L6-v2")

    @pytest.fixture
    def vector_store(self, tmp_path):
        """Create vector store."""
        db_path = tmp_path / "chroma_db"
        store = VectorStore(persist_dir=str(db_path))
        yield store

    def test_ingest_documents_and_embed(
        self, tmp_path, ingestion_engine, embedding_generator, vector_store
    ):
        """Test ingesting documents and creating embeddings."""
        # Create sample documents
        doc_dir = tmp_path / "documents"
        doc_dir.mkdir()

        txt_file = doc_dir / "sample.txt"
        txt_file.write_text("The Matrix is a 1999 science fiction film about artificial intelligence.")

        # Ingest documents
        stats = ingestion_engine.ingest_directory(str(doc_dir))
        assert stats["total"] >= 1
        logger.msg("documents_ingested", count=stats["total"])


class TestRAGErrorHandling:
    """Test error handling in RAG pipeline."""

    @pytest.fixture
    def query_handler(self):
        """Create RAG query handler with mock components."""
        vector_store = Mock()
        embedding_generator = Mock()
        llm_client = ClaudeRAGClient(api_key="test")
        return RAGQueryHandler(vector_store, embedding_generator, llm_client)

    def test_persona_search_error_handling(self, query_handler):
        """Test error handling in persona search."""
        query_handler.vector_store.search_with_cache.side_effect = Exception("Search failed")

        result = query_handler.find_movie_by_persona("tech_enthusiast")

        # Should return empty result, not raise
        assert result["ids"] == [[]]
        assert result["documents"] == [[]]

    def test_time_search_error_handling(self, query_handler):
        """Test error handling in time search."""
        query_handler.vector_store.search_with_cache.side_effect = Exception("Search failed")

        result = query_handler.find_song_by_time("night")

        # Should return empty result, not raise
        assert result["ids"] == [[]]

    def test_intelligent_query_error_handling(self, query_handler):
        """Test error handling in intelligent queries."""
        query_handler.vector_store.search_with_cache.side_effect = Exception("Search failed")

        with pytest.raises(Exception):
            query_handler.intelligent_query("test query", [])


class TestRAGCaching:
    """Test caching behavior in RAG pipeline."""

    @pytest.fixture
    def vector_store(self, tmp_path):
        """Create vector store with cache."""
        db_path = tmp_path / "chroma_db"
        store = VectorStore(persist_dir=str(db_path))
        yield store

    def test_vector_store_search_caching(self, vector_store):
        """Test that searches are cached."""
        # First search should hit database
        result1 = vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=5
        )

        # Second search with same parameters should use cache
        result2 = vector_store.search_with_cache(
            collection_name="test",
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=5
        )

        # Results should be consistent
        assert result1 == result2
        logger.msg("cache_test_success")
