"""LLM integration with Claude API for RAG queries."""
import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from src.logger import get_logger
from src.exceptions import IngestError

logger = get_logger(__name__)


class ClaudeRAGClient:
    """Claude API client for RAG queries."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude RAG client.
        
        Args:
            api_key: Anthropic API key (default: from ANTHROPIC_API_KEY env)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.msg("llm_init_warning", status="no_api_key")
        
        self.model = "claude-opus-4-6"
        self.max_tokens = 1024
        logger.msg("llm_client_init", model=self.model)
    
    def query(self, prompt: str, context: str = "", max_tokens: Optional[int] = None) -> str:
        """Query Claude with context."""
        try:
            import anthropic
        except ImportError:
            logger.msg("anthropic_not_installed", status="fallback")
            return self._fallback_response(prompt)
        
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            
            full_prompt = f"{context}\n\nQuery: {prompt}" if context else prompt
            
            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            response = message.content[0].text
            logger.msg("llm_query_success", prompt_length=len(prompt))
            return response
            
        except Exception as e:
            logger.msg("llm_query_error", error=str(e))
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when API unavailable."""
        return f"[LLM Response Fallback] Query received: {prompt[:100]}..."


class RAGQueryHandler:
    """Handle complex RAG queries."""
    
    def __init__(self, vector_store, embedding_generator, llm_client):
        """Initialize query handler.
        
        Args:
            vector_store: Vector store instance
            embedding_generator: Embedding generator instance
            llm_client: Claude RAG client
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.llm_client = llm_client
        logger.msg("rag_query_handler_init")
    
    def find_movie_by_persona(self, persona: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find movies matching a user persona.
        
        Args:
            persona: User persona (e.g., "tech_enthusiast", "drama_lover")
            top_k: Number of results to return
        
        Returns:
            List of matching movies
        """
        try:
            # Embed persona
            persona_embedding = self.embedding_generator.embed_text(persona)
            
            # Search
            results = self.vector_store.search_with_cache(
                collection_name="movies",
                query_embeddings=[persona_embedding],
                n_results=top_k
            )
            
            logger.msg("movie_search_by_persona", persona=persona, results=len(results.get("ids", [[]])[0]))
            
            return results
        except Exception as e:
            logger.msg("persona_search_error", error=str(e))
            return {"ids": [[]], "documents": [[]], "metadatas": [[]]}
    
    def find_song_by_time(self, time_of_day: str, mood: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find songs suitable for a specific time of day.
        
        Args:
            time_of_day: Time period (morning, afternoon, evening, night)
            mood: Optional mood preference
            top_k: Number of results
        
        Returns:
            List of matching songs
        """
        try:
            query = f"songs for {time_of_day}"
            if mood:
                query += f" with {mood} mood"
            
            # Embed query
            query_embedding = self.embedding_generator.embed_text(query)
            
            # Search
            results = self.vector_store.search_with_cache(
                collection_name="songs",
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            logger.msg("song_search_by_time", time=time_of_day, mood=mood, results=len(results.get("ids", [[]])[0]))
            
            return results
        except Exception as e:
            logger.msg("time_search_error", error=str(e))
            return {"ids": [[]], "documents": [[]], "metadatas": [[]]}
    
    def intelligent_query(self, query: str, context_docs: List[str], top_k: int = 5) -> str:
        """Process intelligent multi-step query using LLM.
        
        Args:
            query: User query
            context_docs: Documents to use as context
            top_k: Number of search results
        
        Returns:
            LLM response with context
        """
        try:
            # Embed query
            query_embedding = self.embedding_generator.embed_text(query)
            
            # Search across all collections
            movie_results = self.vector_store.search_with_cache(
                collection_name="movies",
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            song_results = self.vector_store.search_with_cache(
                collection_name="songs",
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Build context
            context = "Retrieved Context:\n"
            if movie_results.get("documents"):
                context += f"Movies: {' | '.join(movie_results['documents'][0][:3])}\n"
            if song_results.get("documents"):
                context += f"Songs: {' | '.join(song_results['documents'][0][:3])}\n"
            
            # Query LLM
            response = self.llm_client.query(
                prompt=query,
                context=context,
                max_tokens=512
            )
            
            logger.msg("intelligent_query_success", query_length=len(query))
            return response
        
        except Exception as e:
            logger.msg("intelligent_query_error", error=str(e))
            raise IngestError(f"Query failed: {e}")
