"""RAG Application - Main orchestrator for complete RAG pipeline."""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.app import RAGApplication
from src.logger import get_logger
from src.embeddings import EmbeddingGenerator
from src.vector_store import VectorStore
from src.ingestion.engine import DocumentIngestionEngine
from src.llm_integration import ClaudeRAGClient, RAGQueryHandler


logger = get_logger(__name__)


class RAGPipeline:
    """Complete RAG pipeline orchestrator."""

    def __init__(
        self,
        vector_store_path: str = ".chroma",
        embedding_model: str = "all-MiniLM-L6-v2",
        api_key: Optional[str] = None
    ):
        """Initialize RAG pipeline with all components.

        Args:
            vector_store_path: Path to ChromaDB storage
            embedding_model: Sentence transformer model name
            api_key: Anthropic API key (optional)
        """
        self.vector_store_path = vector_store_path
        self.embedding_model = embedding_model

        # Initialize components
        logger.msg("rag_pipeline_init", components="embedding,vector_store,llm")

        self.embedding_generator = EmbeddingGenerator(model_name=embedding_model)
        self.vector_store = VectorStore(persist_dir=vector_store_path)
        self.llm_client = ClaudeRAGClient(api_key=api_key)
        self.query_handler = RAGQueryHandler(
            self.vector_store,
            self.embedding_generator,
            self.llm_client
        )

        self.ingestion_engine = DocumentIngestionEngine(num_workers=4, batch_size=10)

        logger.msg("rag_pipeline_ready")

    def ingest_data_from_file(
        self,
        data_file: str,
        collection_name: str,
        document_field: str = "description",
        metadata_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Ingest data from JSON file into vector store.

        Args:
            data_file: Path to JSON file (expects {"items": [...]})
            collection_name: Name of vector collection
            document_field: Field to use for document text
            metadata_fields: Fields to include as metadata

        Returns:
            Ingestion statistics
        """
        try:
            with open(data_file) as f:
                data = json.load(f)

            # Handle both {"items": [...]} and {"collection_name": [...]} formats
            if "items" in data:
                items = data["items"]
            elif collection_name in data:
                items = data[collection_name]
            else:
                # Assume top-level array
                items = list(data.values())[0] if isinstance(data, dict) else data

            if not items:
                logger.msg("no_items_to_ingest", file=data_file)
                return {"total": 0, "successful": 0, "failed": 0}

            # Prepare documents and metadata
            documents = []
            metadatas = []
            ids = []

            for idx, item in enumerate(items):
                # Get document text
                if document_field in item:
                    doc = item[document_field]
                else:
                    doc = str(item)

                documents.append(doc)
                ids.append(item.get("id", f"doc_{idx}"))

                # Collect metadata
                if metadata_fields:
                    metadata = {
                        field: str(item.get(field, ""))
                        for field in metadata_fields
                    }
                else:
                    # Use all fields as metadata
                    metadata = {
                        k: str(v) for k, v in item.items()
                        if k != document_field and k != "id"
                    }

                metadatas.append(metadata)

            # Generate embeddings
            logger.msg("embedding_generation_start", count=len(documents))
            embeddings = self.embedding_generator.embed_texts(documents)

            # Add to vector store
            logger.msg("adding_to_vector_store", collection=collection_name, count=len(documents))
            self.vector_store.add(
                collection_name=collection_name,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            logger.msg(
                "data_ingested",
                collection=collection_name,
                count=len(documents),
                file=data_file
            )

            return {
                "total": len(documents),
                "successful": len(documents),
                "failed": 0
            }

        except Exception as e:
            logger.msg("ingest_data_error", error=str(e), file=data_file)
            return {"total": 0, "successful": 0, "failed": 1}

    def ingest_directory(
        self,
        directory: str,
        collection_name: str = "documents"
    ) -> Dict[str, Any]:
        """Ingest documents from directory.

        Args:
            directory: Path to directory containing documents
            collection_name: Name of vector collection

        Returns:
            Ingestion statistics
        """
        try:
            stats = self.ingestion_engine.ingest_directory(directory)

            # Get ingested documents
            documents = []
            ids = []
            metadatas = []

            # For now, just log the stats
            logger.msg(
                "directory_ingested",
                directory=directory,
                total=stats["total"],
                successful=stats["successful"],
                failed=stats["failed"]
            )

            return stats

        except Exception as e:
            logger.msg("ingest_directory_error", error=str(e), directory=directory)
            return {"total": 0, "successful": 0, "failed": 1}

    def find_movies_by_persona(
        self,
        persona: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find movies matching a user persona.

        Args:
            persona: User persona description
            top_k: Number of results

        Returns:
            List of matching movies with scores
        """
        logger.msg("find_movies_by_persona", persona=persona, top_k=top_k)

        results = self.query_handler.find_movie_by_persona(persona, top_k=top_k)

        # Format results
        formatted = []
        if results.get("ids") and results["ids"][0]:
            for idx, doc_id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": doc_id,
                    "title": results["metadatas"][0][idx].get("title", "Unknown"),
                    "description": results["documents"][0][idx] if results["documents"] else "",
                    "metadata": results["metadatas"][0][idx] if results["metadatas"] else {}
                })

        logger.msg("find_movies_success", count=len(formatted))
        return formatted

    def find_songs_by_time(
        self,
        time_of_day: str,
        mood: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find songs suitable for a specific time.

        Args:
            time_of_day: Time period (morning, afternoon, evening, night)
            mood: Optional mood preference
            top_k: Number of results

        Returns:
            List of matching songs
        """
        logger.msg("find_songs_by_time", time=time_of_day, mood=mood, top_k=top_k)

        results = self.query_handler.find_song_by_time(time_of_day, mood=mood, top_k=top_k)

        # Format results
        formatted = []
        if results.get("ids") and results["ids"][0]:
            for idx, doc_id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": doc_id,
                    "title": results["metadatas"][0][idx].get("title", "Unknown"),
                    "artist": results["metadatas"][0][idx].get("artist", "Unknown"),
                    "description": results["documents"][0][idx] if results["documents"] else "",
                    "metadata": results["metadatas"][0][idx] if results["metadatas"] else {}
                })

        logger.msg("find_songs_success", count=len(formatted))
        return formatted

    def query(
        self,
        query: str,
        context_collections: Optional[List[str]] = None,
        top_k: int = 5
    ) -> str:
        """Execute intelligent query across RAG system.

        Args:
            query: User query
            context_collections: Collections to search (default: all)
            top_k: Number of results per collection

        Returns:
            LLM response with context
        """
        logger.msg("intelligent_query", query_length=len(query), top_k=top_k)

        # Get context from vector store
        context_docs = []

        try:
            response = self.query_handler.intelligent_query(
                query=query,
                context_docs=context_docs,
                top_k=top_k
            )

            logger.msg("query_success")
            return response

        except Exception as e:
            logger.msg("query_error", error=str(e))
            return f"Query failed: {str(e)}"

    def setup_sample_data(self):
        """Set up sample movie and song data for testing."""
        logger.msg("setup_sample_data_start")

        # Ingest movies
        self.ingest_data_from_file(
            data_file="data/movies.json",
            collection_name="movies",
            document_field="description",
            metadata_fields=["title", "genre", "personas", "year", "rating"]
        )

        # Ingest songs
        self.ingest_data_from_file(
            data_file="data/songs.json",
            collection_name="songs",
            document_field="description",
            metadata_fields=["title", "artist", "genre", "mood", "best_time", "year"]
        )

        logger.msg("setup_sample_data_complete")

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on RAG pipeline."""
        health = {
            "status": "healthy",
            "components": {}
        }

        try:
            # Check embedding generator
            test_embedding = self.embedding_generator.embed_text("test")
            health["components"]["embeddings"] = "ok" if test_embedding else "error"
        except Exception as e:
            health["components"]["embeddings"] = f"error: {str(e)}"
            health["status"] = "unhealthy"

        try:
            # Check vector store
            collections = self.vector_store.list_collections()
            health["components"]["vector_store"] = "ok"
            health["collections"] = collections
        except Exception as e:
            health["components"]["vector_store"] = f"error: {str(e)}"
            health["status"] = "unhealthy"

        try:
            # Check LLM client
            health["components"]["llm"] = "ok" if self.llm_client.api_key else "warning: no api_key"
        except Exception as e:
            health["components"]["llm"] = f"error: {str(e)}"

        logger.msg("health_check", result=health)
        return health


def create_rag_pipeline(
    vector_store_path: str = ".chroma",
    embedding_model: str = "all-MiniLM-L6-v2"
) -> RAGPipeline:
    """Factory function to create RAG pipeline."""
    return RAGPipeline(
        vector_store_path=vector_store_path,
        embedding_model=embedding_model
    )


# Global RAG pipeline instance
_rag_instance = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create global RAG pipeline instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = create_rag_pipeline()
    return _rag_instance
