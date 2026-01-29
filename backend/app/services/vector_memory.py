"""
Vector Memory Service using Redis + OpenAI Embeddings.

Stores conversation turns as embeddings with metadata and provides
similarity search to retrieve relevant past context per user.
"""

from typing import List, Optional, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_redis import RedisVectorStore
except Exception as e:
    # Defer import errors for environments without optional deps
    logger.warning(f"Vector memory optional deps not fully available: {e}")
    OpenAIEmbeddings = None  # type: ignore
    RedisVectorStore = None  # type: ignore


class VectorMemory:
    """Encapsulates Redis vector store operations per user."""

    def __init__(self):
        self.enabled = bool(settings.redis_url and settings.openai_api_key and OpenAIEmbeddings and RedisVectorStore)
        self._embeddings = None
        self._redis = None

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
                logger.error(f"Failed to initialize VectorMemory: {e}")
                self.enabled = False

    def add_turn(self, user_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a conversation turn to vector memory."""
        if not self.enabled or not text:
            return
        try:
            # Use namespace to avoid collisions and allow filters
            met = {"user_id": user_id, **(metadata or {})}
            RedisVectorStore.from_texts(
                texts=[text],
                embedding=self._embeddings,
                redis_url=settings.redis_url,
                index_name=settings.redis_index_name,
                metadatas=[met],
            )
        except Exception as e:
            logger.warning(f"VectorMemory add_turn failed: {e}")

    def search(self, user_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar past context for a user."""
        if not self.enabled or not query:
            return []
        try:
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
            return formatted
        except Exception as e:
            logger.warning(f"VectorMemory search failed: {e}")
            return []

    def filtered_search(self, user_id: str, query: str, project_id: Optional[str] = None, 
                       task_id: Optional[str] = None, agent_type: Optional[str] = None,
                       k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar past context with project/task/agent type filtering."""
        if not self.enabled or not query:
            return []
        try:
            # Build filter combining user_id and optional metadata filters
            filter_dict = {"user_id": user_id}
            if project_id:
                filter_dict["project_id"] = project_id
            if task_id:
                filter_dict["task_id"] = task_id
            if agent_type:
                filter_dict["agent_type"] = agent_type
            
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
            return formatted
        except Exception as e:
            logger.warning(f"VectorMemory filtered_search failed: {e}")
            return []
