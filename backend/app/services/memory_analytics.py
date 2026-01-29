"""
Memory Analytics Service for Conversation Insights.

Provides statistics and insights about conversation memory,
including message counts, compaction history, and memory usage.
"""

from google.cloud import firestore
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.firebase import get_firestore_client
from app.services.conversation_memory import ConversationMemory
from app.services.vector_memory import VectorMemory
import logging

logger = logging.getLogger(__name__)


class MemoryAnalytics:
    """Provides analytics and insights about conversation memory."""
    
    def __init__(self, user_id: str):
        """
        Initialize analytics service for a user.
        
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
    
    def get_message_count(self) -> int:
        """
        Get total count of messages for a user.
        
        Returns:
            Total number of message documents
        """
        try:
            # Use aggregation for efficient count
            count = self.conversations_ref.count().get()[0][0].value
            return int(count) if count else 0
        except Exception as e:
            logger.warning(f"Failed to get message count for user {self.user_id}: {e}")
            return 0
    
    def get_summary_count(self) -> int:
        """
        Get total count of conversation summaries.
        
        Returns:
            Number of summary documents
        """
        try:
            count = self.summaries_ref.count().get()[0][0].value
            return int(count) if count else 0
        except Exception as e:
            logger.warning(f"Failed to get summary count for user {self.user_id}: {e}")
            return 0
    
    def get_message_timeline(self, days: int = 30) -> Dict[str, int]:
        """
        Get message count by date for the past N days.
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dict mapping dates to message counts
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = self.conversations_ref.where(
                "timestamp", ">=", cutoff_date
            ).stream()
            
            timeline = {}
            for doc in query:
                timestamp = doc.get("timestamp")
                if timestamp:
                    date_str = timestamp.strftime("%Y-%m-%d")
                    timeline[date_str] = timeline.get(date_str, 0) + 1
            
            return timeline
        except Exception as e:
            logger.warning(f"Failed to get message timeline for user {self.user_id}: {e}")
            return {}
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive memory statistics for a user.
        
        Returns:
            Dict with message count, summary count, vector status, etc.
        """
        try:
            message_count = self.get_message_count()
            summary_count = self.get_summary_count()
            timeline = self.get_message_timeline(days=7)  # Past week
            
            # Get vector memory status
            vec_mem = VectorMemory()
            vec_status = vec_mem.get_status()
            
            # Calculate stats
            total_messages_week = sum(timeline.values())
            avg_per_day = total_messages_week / 7 if total_messages_week > 0 else 0
            
            return {
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "messages": {
                    "total": message_count,
                    "summaries": summary_count,
                    "avg_per_day_week": round(avg_per_day, 2),
                    "past_week": total_messages_week,
                },
                "vector_memory": {
                    "enabled": vec_status["enabled"],
                    "error_count": vec_status["error_count"],
                    "last_error": vec_status["last_error"],
                },
                "compaction": {
                    "status": "healthy" if message_count <= 100 else "may_need_compaction",
                    "messages_since_last_compact": message_count,
                    "recommendation": "Run compaction" if message_count > 50 else "No action needed",
                },
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats for user {self.user_id}: {e}")
            return {}
    
    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for a specific project.
        
        Args:
            project_id: The project ID
            
        Returns:
            Project-specific memory statistics
        """
        try:
            # Query messages with project_id in metadata
            query = self.conversations_ref.where(
                "metadata.project_id", "==", project_id
            ).stream()
            
            messages = []
            for doc in query:
                messages.append(doc.to_dict())
            
            return {
                "project_id": project_id,
                "message_count": len(messages),
                "timestamp": datetime.now().isoformat(),
                "has_data": len(messages) > 0,
            }
        except Exception as e:
            logger.warning(f"Failed to get project stats for {project_id}: {e}")
            return {
                "project_id": project_id,
                "message_count": 0,
                "error": str(e),
            }
    
    def get_task_stats(self, task_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for a specific task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task-specific memory statistics
        """
        try:
            # Query messages with task_id in metadata
            query = self.conversations_ref.where(
                "metadata.task_id", "==", task_id
            ).stream()
            
            messages = []
            for doc in query:
                messages.append(doc.to_dict())
            
            return {
                "task_id": task_id,
                "message_count": len(messages),
                "timestamp": datetime.now().isoformat(),
                "has_data": len(messages) > 0,
            }
        except Exception as e:
            logger.warning(f"Failed to get task stats for {task_id}: {e}")
            return {
                "task_id": task_id,
                "message_count": 0,
                "error": str(e),
            }
    
    def get_agent_stats(self) -> Dict[str, int]:
        """
        Get message distribution by agent type.
        
        Returns:
            Dict mapping agent types to message counts
        """
        try:
            query = self.conversations_ref.stream()
            agent_counts = {}
            
            for doc in query:
                metadata = doc.get("metadata", {})
                agents = metadata.get("agents_called", [])
                
                for agent in agents:
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            return agent_counts
        except Exception as e:
            logger.warning(f"Failed to get agent stats for user {self.user_id}: {e}")
            return {}
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation messages.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of recent message documents
        """
        try:
            query = (
                self.conversations_ref
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            
            messages = []
            for doc in query:
                msg_data = doc.to_dict()
                msg_data["doc_id"] = doc.id
                messages.append(msg_data)
            
            return messages
        except Exception as e:
            logger.warning(f"Failed to get recent messages for user {self.user_id}: {e}")
            return []
