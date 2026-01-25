"""
Conversation Memory Service for LangGraph Multi-Agent System.

This service manages conversation history persistence in Firestore,
allowing the agent to maintain context across sessions.
"""

from google.cloud import firestore
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.firebase import get_firestore_client
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history in Firestore."""

    def __init__(self, user_id: str):
        """
        Initialize conversation memory for a specific user.

        Args:
            user_id: The user's Firebase UID
        """
        self.user_id = user_id
        self.db = get_firestore_client()
        self.conversations_ref = (
            self.db.collection("conversations")
            .document(user_id)
            .collection("messages")
        )

    def save_message(
        self,
        user_message: str,
        agent_response: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Save a conversation turn to Firestore.

        Args:
            user_message: The user's message
            agent_response: The agent's response
            metadata: Optional metadata (agents_called, intent, etc.)
        """
        try:
            self.conversations_ref.add({
                "user_message": user_message,
                "agent_response": agent_response,
                "metadata": metadata or {},
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Saved conversation for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")

    def get_recent_history(self, limit: int = 10) -> List[dict]:
        """
        Get recent conversation history.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of conversation messages (oldest first)
        """
        try:
            docs = (
                self.conversations_ref
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )

            history = []
            for doc in docs:
                data = doc.to_dict()
                history.append({
                    "id": doc.id,
                    "user_message": data.get("user_message"),
                    "agent_response": data.get("agent_response"),
                    "timestamp": data.get("timestamp"),
                    "metadata": data.get("metadata", {})
                })

            # Return oldest first for chronological order
            return list(reversed(history))

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []

    def get_context_summary(self, max_messages: int = 5) -> str:
        """
        Generate a summary of recent conversation for context.

        Args:
            max_messages: Maximum number of messages to include

        Returns:
            String summary of recent conversation
        """
        history = self.get_recent_history(max_messages)

        if not history:
            return "No previous conversation history."

        summary = "Recent conversation:\n"
        for msg in history:
            user_msg = msg["user_message"][:100]
            agent_msg = msg["agent_response"][:100]
            summary += f"User: {user_msg}...\n"
            summary += f"Assistant: {agent_msg}...\n\n"

        return summary

    def clear_history(self) -> None:
        """Clear all conversation history for the user."""
        try:
            docs = self.conversations_ref.stream()
            for doc in docs:
                doc.reference.delete()
            logger.info(f"Cleared conversation history for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error clearing conversation history: {str(e)}")
