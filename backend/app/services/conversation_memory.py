"""
Conversation Memory Service for LangGraph Multi-Agent System.

This service manages conversation history persistence in Firestore,
allowing the agent to maintain context across sessions.
"""

from google.cloud import firestore
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.firebase import get_firestore_client
from app.services.vector_memory import VectorMemory
from langchain_openai import ChatOpenAI
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
        self.summaries_ref = (
            self.db.collection("conversations")
            .document(user_id)
            .collection("summaries")
        )
        self.vector_memory = VectorMemory()
        self.llm = ChatOpenAI(temperature=0.2)

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
            doc_ref = self.conversations_ref.add({
                "user_message": user_message,
                "agent_response": agent_response,
                "metadata": metadata or {},
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Saved conversation for user {self.user_id}")

            # Index combined turn in vector memory
            turn_text = f"User: {user_message}\nAssistant: {agent_response}"
            self.vector_memory.add_turn(self.user_id, turn_text, metadata)
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

    def summarize_and_compact(self, retain_last: int = 20) -> Optional[str]:
        """Summarize older messages and store compacted summary.

        Args:
            retain_last: Number of most recent messages to retain verbatim.

        Returns:
            The summary text if created, else None.
        """
        try:
            # Fetch more history
            docs = (
                self.conversations_ref
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(200)
                .stream()
            )
            items = list(docs)
            if len(items) <= retain_last:
                return None

            # Older messages to summarize
            to_summarize = items[retain_last:]
            to_summarize_text = []
            for doc in reversed(to_summarize):  # chronological
                data = doc.to_dict()
                to_summarize_text.append(
                    f"User: {data.get('user_message','')}\nAssistant: {data.get('agent_response','')}"
                )
            prompt = (
                "Summarize the following conversation turns into a concise context summary (bullet points ok).\n" 
                "Focus on user goals, decisions, preferences, and unresolved items.\n\n" +
                "\n\n".join(to_summarize_text)
            )
            summary_resp = self.llm.invoke([
                ("system", "You are a helpful assistant that writes concise summaries."),
                ("human", prompt)
            ])
            summary_text = summary_resp.content if hasattr(summary_resp, 'content') else str(summary_resp)

            # Store summary document
            self.summaries_ref.add({
                "summary": summary_text,
                "created_at": firestore.SERVER_TIMESTAMP,
                "message_count": len(to_summarize),
            })

            # Optionally delete older messages (soft-archive)
            batch = self.db.batch()
            for doc in to_summarize:
                batch.delete(doc.reference)
            batch.commit()

            logger.info(f"Compacted {len(to_summarize)} messages into a summary for user {self.user_id}")
            return summary_text
        except Exception as e:
            logger.error(f"Error during summarize_and_compact: {e}")
            return None

    def clear_history(self) -> None:
        """Clear all conversation history for the user."""
        try:
            docs = self.conversations_ref.stream()
            for doc in docs:
                doc.reference.delete()
            logger.info(f"Cleared conversation history for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error clearing conversation history: {str(e)}")
