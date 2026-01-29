"""
Vector Memory Service using Redis + OpenAI Embeddings.

Stores conversation turns as embeddings with metadata and provides
similarity search to retrieve relevant past context per user.
"""

from typing import List, Optional, Dict, Any
from app.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_redis import RedisVectorStore
except Exception as e:
    # Defer import errors for environments without optional deps
    logger.warning(f"Vector memory optional deps not fully available: {e}")
    OpenAIEmbeddings = None  # type: ignore
    RedisVectorStore = None  # type: ignore


class VectorMemoryError(Exception):
    """Custom exception for vector memory operations."""
    pass


class VectorMemory:
    """Encapsulates Redis vector store operations per user."""

    def __init__(self):
        self.enabled = bool(settings.redis_url and settings.openai_api_key and OpenAIEmbeddings and RedisVectorStore)
        self._embeddings = None
        self._redis = None
        self._last_error: Optional[str] = None
        self._error_count: int = 0
        self._failed_at: Optional[datetime] = None

        if self.enabled:
            try:
                self._embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
                # Instantiate a vector store handle without creating the index yet
                # The Redis vectorstore uses a single index; we'll use metadata filters per user
                self._redis = RedisVectorStore(
                    embedding=self._embeddings,
                    redis_url=settings.redis_url,
                    index_name=settings.redis_index_name,
                )
                logger.info("VectorMemory initialized with Redis index '%s'", settings.redis_index_name)
            except Exception as e:
                error_msg = f"Failed to initialize VectorMemory: {type(e).__name__}: {str(e)}"
                logger.error(error_msg)
                self.enabled = False
                self._last_error = error_msg
                self._failed_at = datetime.now()

    def _handle_error(self, operation: str, error: Exception, user_id: Optional[str] = None) -> None:
        """
        Handle and log vector memory errors with contextual information.
        
        Args:
            operation: The operation that failed (e.g., 'add_turn', 'search')
            error: The exception that was raised
            user_id: Optional user context for debugging
        """
        self._error_count += 1
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Determine error severity and log accordingly
        if isinstance(error, (ConnectionError, TimeoutError)):
            # Connection issues - log as warning
            logger.warning(
                f"VectorMemory {operation} - Connection error (attempt {self._error_count}): "
                f"{error_type}: {error_msg}" + (f" (user: {user_id})" if user_id else "")
            )
        elif isinstance(error, ValueError):
            # Invalid input - log as warning
            logger.warning(
                f"VectorMemory {operation} - Invalid input: {error_msg}" + 
                (f" (user: {user_id})" if user_id else "")
            )
        else:
            # Other errors - log as error
            logger.error(
                f"VectorMemory {operation} failed: {error_type}: {error_msg}" + 
                (f" (user: {user_id})" if user_id else ""),
                exc_info=False  # Don't include full stack trace for expected failures
            )
        
        self._last_error = f"{error_type}: {error_msg}"
        self._failed_at = datetime.now()

    def add_turn(self, user_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a conversation turn to vector memory.
        
        Args:
            user_id: User identifier
            text: Conversation text to embed
            metadata: Optional metadata to attach
            
        Returns:
            True if successfully added, False otherwise
        """
        if not self.enabled or not text or not user_id:
            if not self.enabled:
                logger.debug("VectorMemory disabled - skipping add_turn")
            return False
        
        try:
            # Validate text length (prevent excessive indexing)
            if len(text) > 10000:
                logger.warning(f"VectorMemory add_turn - Text exceeds 10K chars, truncating for user {user_id}")
                text = text[:10000]
            
            # Use namespace to avoid collisions and allow filters
            met = {"user_id": user_id, **(metadata or {})}
            RedisVectorStore.from_texts(
                texts=[text],
                embedding=self._embeddings,
                redis_url=settings.redis_url,
                index_name=settings.redis_index_name,
                metadatas=[met],
            )
            
            # Reset error count on success
            if self._error_count > 0:
                logger.info(f"VectorMemory recovered after {self._error_count} errors")
                self._error_count = 0
            
            return True
            
        except Exception as e:
            self._handle_error("add_turn", e, user_id=user_id)
            return False

    def search(self, user_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar past context for a user.
        
        Args:
            user_id: User identifier
            query: Query text for similarity search
            k: Number of results to return
            
        Returns:
            List of similar documents with scores, or empty list on error
        """
        if not self.enabled or not query or not user_id:
            if not self.enabled:
                logger.debug("VectorMemory disabled - returning empty search results")
            return []
        
        try:
            # Validate query length
            if len(query) > 5000:
                logger.debug(f"VectorMemory search - Query exceeds 5K chars, truncating for user {user_id}")
                query = query[:5000]
            
            results = self._redis.similarity_search_with_score(
                query,
                k=k,
                filter={"user_id": user_id},
            )
            
            formatted = []
            for doc, score in results:
                formatted.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata or {},
                    "score": float(score),
                })
            
            # Reset error count on success
            if self._error_count > 0:
                logger.info(f"VectorMemory recovered after {self._error_count} errors")
                self._error_count = 0
            
            return formatted
            
        except Exception as e:
            self._handle_error("search", e, user_id=user_id)
            return []

    def filtered_search(self, user_id: str, query: str, project_id: Optional[str] = None, 
                       task_id: Optional[str] = None, agent_type: Optional[str] = None,
                       k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar past context with project/task/agent type filtering.
        
        Args:
            user_id: User identifier
            query: Query text for similarity search
            project_id: Optional project filter
            task_id: Optional task filter
            agent_type: Optional agent type filter
            k: Number of results to return
            
        Returns:
            List of filtered similar documents with scores, or empty list on error
        """
        if not self.enabled or not query or not user_id:
            if not self.enabled:
                logger.debug("VectorMemory disabled - returning empty filtered search results")
            return []
        
        try:
            # Validate query length
            if len(query) > 5000:
                logger.debug(f"VectorMemory filtered_search - Query exceeds 5K chars, truncating")
                query = query[:5000]
            
            # Build filter combining user_id and optional metadata filters
            filter_dict = {"user_id": user_id}
            if project_id:
                filter_dict["project_id"] = project_id
            if task_id:
                filter_dict["task_id"] = task_id
            if agent_type:
                filter_dict["agent_type"] = agent_type
            
            logger.debug(f"VectorMemory filtered_search with filters: {filter_dict}")
            
            results = self._redis.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict,
            )
            
            formatted = []
            for doc, score in results:
                formatted.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata or {},
                    "score": float(score),
                })
            
            # Reset error count on success
            if self._error_count > 0:
                logger.info(f"VectorMemory recovered after {self._error_count} errors")
                self._error_count = 0
            
            return formatted
            
        except Exception as e:
            self._handle_error("filtered_search", e, user_id=user_id)
            return []

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of vector memory service.
        
        Returns:
            Status dict with enabled state, error info, and metrics
        """
        return {
            "enabled": self.enabled,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "last_error_at": self._failed_at.isoformat() if self._failed_at else None,
            "redis_url": settings.redis_url[:20] + "..." if settings.redis_url else None,
        }
