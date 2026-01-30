"""
Enhanced Conversation Service with conversation-by-conversation tracking.

Manages conversations with proper context, summaries, and long-term storage.
Uses Firebase for persistent storage and Redis for quick retrieval.
"""

from google.cloud import firestore
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4
import json
import logging

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.firebase import get_firestore_client
from app.config import settings


class ConversationService:
    """Manages individual conversations with full context and history."""

    def __init__(self, user_id: str):
        """
        Initialize conversation service for a user.

        Args:
            user_id: Firebase UID
        """
        self.user_id = user_id
        self.db = get_firestore_client()
        self.user_conversations_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("conversations")
        )
        
        # Redis setup for fast retrieval
        self.redis_client = None
        if REDIS_AVAILABLE and settings.redis_url:
            try:
                self.redis_client = redis.Redis.from_url(
                    settings.redis_url,
                    db=1,  # Use db 1 for conversations
                    decode_responses=True
                )
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                self.redis_client = None

    def _get_redis_key(self, conversation_id: str) -> str:
        """Get Redis key for a conversation."""
        return f"conv:{self.user_id}:{conversation_id}"

    def create_conversation(
        self,
        title: Optional[str] = None,
        initial_message: Optional[str] = None
    ) -> str:
        """
        Create a new conversation.

        Args:
            title: Optional conversation title (auto-generated from first message if not provided)
            initial_message: Optional first user message

        Returns:
            Conversation ID
        """
        try:
            conversation_id = str(uuid4())
            now = datetime.utcnow()

            # If no title provided and has initial message, generate from message
            if not title and initial_message:
                # Use first 50 chars of message as title
                title = initial_message[:50].strip()
                if len(initial_message) > 50:
                    title += "..."

            conversation_doc = {
                "id": conversation_id,
                "user_id": self.user_id,
                "title": title or "New Conversation",
                "messages": [],
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "archived": False,
                "metadata": {
                    "message_count": 0,
                    "agents_used": [],
                    "tasks_created": []
                }
            }

            # Save to Firestore
            self.user_conversations_ref.document(conversation_id).set(conversation_doc)
            logger.info(f"Created conversation {conversation_id} for user {self.user_id}")

            # Cache in Redis
            if self.redis_client:
                try:
                    self.redis_client.setex(
                        self._get_redis_key(conversation_id),
                        3600,  # 1 hour TTL
                        json.dumps(conversation_doc, default=str)
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache in Redis: {e}")

            return conversation_id

        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise

    def update_conversation_title(self, conversation_id: str, title: str) -> None:
        """
        Update conversation title.

        Args:
            conversation_id: ID of the conversation
            title: New title for the conversation
        """
        try:
            conv_ref = self.user_conversations_ref.document(conversation_id)
            conv_ref.update({
                "title": title,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
            # Invalidate Redis cache
            if self.redis_client:
                try:
                    self.redis_client.delete(self._get_redis_key(conversation_id))
                except Exception as e:
                    logger.warning(f"Failed to invalidate Redis cache: {e}")
            
            logger.info(f"Updated conversation {conversation_id} title to: {title}")
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            # Don't raise - title update failure shouldn't break message sending

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to a conversation.

        Args:
            conversation_id: ID of the conversation
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (agent, intent, etc.)
        """
        try:
            timestamp = datetime.utcnow()
            message = {
                "role": role,
                "content": content,
                "timestamp": timestamp,  # Use actual datetime, not SERVER_TIMESTAMP
                "metadata": metadata or {}
            }

            # Update Firestore - add message and update timestamp
            conv_ref = self.user_conversations_ref.document(conversation_id)
            conv_ref.update({
                "messages": firestore.ArrayUnion([message]),
                "updated_at": firestore.SERVER_TIMESTAMP,
                "metadata.message_count": firestore.Increment(1)
            })

            logger.info(f"Added {role} message to conversation {conversation_id}")

            # If this is the first user message and title is still "New Conversation", auto-generate title
            if role == "user":
                conversation = self.get_conversation(conversation_id)
                if conversation and conversation.get("title") == "New Conversation":
                    # Generate title from first 60 chars of user message
                    title = content[:60].strip()
                    if len(content) > 60:
                        title += "..."
                    # Update title (non-blocking if fails)
                    self.update_conversation_title(conversation_id, title)

            # Invalidate Redis cache so next fetch gets fresh data
            if self.redis_client:
                try:
                    self.redis_client.delete(self._get_redis_key(conversation_id))
                except Exception as e:
                    logger.warning(f"Failed to invalidate Redis cache: {e}")

        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get a full conversation with all messages.

        Tries Redis first (fast), then Firestore (persistent).

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation dict with all messages, or None if not found
        """
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    cached = self.redis_client.get(self._get_redis_key(conversation_id))
                    if cached:
                        logger.debug(f"Retrieved conversation {conversation_id} from Redis")
                        return json.loads(cached)
                except Exception as e:
                    logger.warning(f"Failed to retrieve from Redis: {e}")

            # Fall back to Firestore
            doc = self.user_conversations_ref.document(conversation_id).get()
            if doc.exists:
                conversation = doc.to_dict()
                
                # Cache in Redis for next time
                if self.redis_client:
                    try:
                        self.redis_client.setex(
                            self._get_redis_key(conversation_id),
                            3600,
                            json.dumps(conversation, default=str)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cache in Redis: {e}")

                return conversation

            logger.warning(f"Conversation {conversation_id} not found")
            return None

        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
            return None

    def list_conversations(
        self,
        limit: int = 50,
        archived: bool = False
    ) -> List[Dict]:
        """
        List all conversations for the user.

        Args:
            limit: Max conversations to return
            archived: Include archived conversations

        Returns:
            List of conversations with messages excluded (for quick loading)
        """
        try:
            # Avoid composite index requirement by ordering only, then filtering in memory
            query = self.user_conversations_ref.order_by(
                "updated_at",
                direction=firestore.Query.DESCENDING
            ).limit(max(limit * 3, limit))

            conversations = []
            for doc in query.stream():
                conv = doc.to_dict()

                # Filter archived flag in memory
                if conv.get("archived", False) != archived:
                    continue

                # Don't include full message list for list view
                if "messages" in conv:
                    message_count = len(conv["messages"])
                    conv["messages"] = []  # Empty for list view
                    conv["message_count"] = message_count

                conversations.append(conv)

                if len(conversations) >= limit:
                    break

            logger.info(f"Retrieved {len(conversations)} conversations for user {self.user_id}")
            return conversations

        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []

    def get_conversation_context(
        self,
        conversation_id: str,
        max_messages: int = 20
    ) -> str:
        """
        Get conversation context as a formatted string for the agent.

        Args:
            conversation_id: ID of the conversation
            max_messages: Max messages to include (most recent)

        Returns:
            Formatted conversation context string
        """
        try:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                return ""

            messages = conversation.get("messages", [])
            # Get most recent N messages
            recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

            context_lines = ["# Conversation Context"]
            context_lines.append(f"Title: {conversation.get('title', 'Unknown')}")
            context_lines.append(f"Messages so far: {len(messages)}")
            context_lines.append("\n## Recent Messages:")

            for msg in recent_messages:
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                context_lines.append(f"\n{role}: {content}")

            return "\n".join(context_lines)

        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return ""

    def update_conversation_metadata(
        self,
        conversation_id: str,
        metadata_updates: Dict[str, Any]
    ) -> None:
        """
        Update conversation metadata (agents used, tasks created, etc.).

        Args:
            conversation_id: ID of the conversation
            metadata_updates: Dict of metadata to merge/update
        """
        try:
            conv_ref = self.user_conversations_ref.document(conversation_id)
            
            # Get current metadata
            conv = conv_ref.get()
            if not conv.exists:
                logger.warning(f"Conversation {conversation_id} not found")
                return

            current_metadata = conv.to_dict().get("metadata", {})
            
            # Merge updates
            for key, value in metadata_updates.items():
                if key in current_metadata and isinstance(current_metadata[key], list):
                    # For lists, append if not already present
                    if isinstance(value, list):
                        for item in value:
                            if item not in current_metadata[key]:
                                current_metadata[key].append(item)
                    else:
                        if value not in current_metadata[key]:
                            current_metadata[key].append(value)
                else:
                    current_metadata[key] = value

            # Update in Firestore
            conv_ref.update({
                "metadata": current_metadata,
                "updated_at": firestore.SERVER_TIMESTAMP
            })

            logger.info(f"Updated metadata for conversation {conversation_id}")

            # Invalidate Redis cache
            if self.redis_client:
                try:
                    self.redis_client.delete(self._get_redis_key(conversation_id))
                except Exception as e:
                    logger.warning(f"Failed to invalidate Redis cache: {e}")

        except Exception as e:
            logger.error(f"Error updating conversation metadata: {e}")
            raise

    def archive_conversation(self, conversation_id: str) -> None:
        """Archive a conversation (soft delete)."""
        try:
            self.user_conversations_ref.document(conversation_id).update({
                "archived": True,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Archived conversation {conversation_id}")

            if self.redis_client:
                try:
                    self.redis_client.delete(self._get_redis_key(conversation_id))
                except Exception as e:
                    logger.warning(f"Failed to invalidate Redis cache: {e}")

        except Exception as e:
            logger.error(f"Error archiving conversation: {e}")
            raise

    def delete_conversation(self, conversation_id: str) -> None:
        """Permanently delete a conversation."""
        try:
            self.user_conversations_ref.document(conversation_id).delete()
            logger.info(f"Deleted conversation {conversation_id}")

            if self.redis_client:
                try:
                    self.redis_client.delete(self._get_redis_key(conversation_id))
                except Exception as e:
                    logger.warning(f"Failed to invalidate Redis cache: {e}")

        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise
