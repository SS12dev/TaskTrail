"""
Conversation Export Service.

Provides functionality to export conversation history in various formats
(JSON, CSV, Markdown) for user backup and sharing.
"""

import csv
import json
from io import StringIO
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.firebase import get_firestore_client
from app.services.conversation_memory import ConversationMemory
import logging

logger = logging.getLogger(__name__)


class ConversationExporter:
    """Exports conversation history in various formats."""
    
    def __init__(self, user_id: str):
        """
        Initialize the exporter for a user.
        
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
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all conversation messages.
        
        Args:
            limit: Maximum number of messages (None for all)
            
        Returns:
            List of message documents with timestamps
        """
        try:
            query = (
                self.conversations_ref
                .order_by("timestamp", direction=self.db._client.constants.CollectionReference.Order.DESCENDING)
            )
            
            if limit:
                query = query.limit(limit)
            
            messages = []
            for doc in query.stream():
                msg = doc.to_dict()
                msg["id"] = doc.id
                messages.append(msg)
            
            # Reverse to get chronological order (oldest first)
            return list(reversed(messages))
        except Exception as e:
            logger.error(f"Error retrieving messages for user {self.user_id}: {e}")
            return []
    
    def export_json(self, limit: Optional[int] = None, pretty: bool = True) -> str:
        """
        Export conversation as JSON.
        
        Args:
            limit: Maximum number of messages (None for all)
            pretty: Whether to format with indentation
            
        Returns:
            JSON string
        """
        try:
            messages = self.get_messages(limit)
            
            export_data = {
                "user_id": self.user_id,
                "exported_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": messages,
            }
            
            indent = 2 if pretty else None
            return json.dumps(export_data, indent=indent, default=str)
        
        except Exception as e:
            logger.error(f"Error exporting JSON for user {self.user_id}: {e}")
            return json.dumps({"error": str(e)})
    
    def export_csv(self, limit: Optional[int] = None) -> str:
        """
        Export conversation as CSV.
        
        Args:
            limit: Maximum number of messages (None for all)
            
        Returns:
            CSV string
        """
        try:
            messages = self.get_messages(limit)
            
            output = StringIO()
            fieldnames = [
                "timestamp",
                "user_message",
                "agent_response",
                "agents_called",
                "intent",
                "action",
                "project_id",
                "task_id",
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for msg in messages:
                row = {
                    "timestamp": msg.get("timestamp", ""),
                    "user_message": msg.get("user_message", ""),
                    "agent_response": msg.get("agent_response", ""),
                    "agents_called": ",".join(msg.get("metadata", {}).get("agents_called", [])),
                    "intent": msg.get("metadata", {}).get("intent", ""),
                    "action": msg.get("metadata", {}).get("action", ""),
                    "project_id": msg.get("metadata", {}).get("project_id", ""),
                    "task_id": msg.get("metadata", {}).get("task_id", ""),
                }
                writer.writerow(row)
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Error exporting CSV for user {self.user_id}: {e}")
            return f"Error: {str(e)}"
    
    def export_markdown(self, limit: Optional[int] = None) -> str:
        """
        Export conversation as Markdown.
        
        Args:
            limit: Maximum number of messages (None for all)
            
        Returns:
            Markdown formatted string
        """
        try:
            messages = self.get_messages(limit)
            
            output = []
            output.append(f"# Conversation Export")
            output.append(f"**Exported:** {datetime.now().isoformat()}")
            output.append(f"**Total Messages:** {len(messages)}")
            output.append("")
            
            for i, msg in enumerate(messages, 1):
                timestamp = msg.get("timestamp", "Unknown")
                user_msg = msg.get("user_message", "")
                agent_resp = msg.get("agent_response", "")
                metadata = msg.get("metadata", {})
                
                output.append(f"## Turn {i}")
                output.append(f"**Time:** {timestamp}")
                output.append("")
                
                output.append("### User Message")
                output.append(f"> {user_msg}")
                output.append("")
                
                output.append("### Agent Response")
                output.append(f"{agent_resp}")
                output.append("")
                
                # Add metadata if present
                if metadata:
                    agents = metadata.get("agents_called", [])
                    intent = metadata.get("intent")
                    action = metadata.get("action")
                    project_id = metadata.get("project_id")
                    task_id = metadata.get("task_id")
                    
                    meta_items = []
                    if agents:
                        meta_items.append(f"**Agents:** {', '.join(agents)}")
                    if intent:
                        meta_items.append(f"**Intent:** {intent}")
                    if action:
                        meta_items.append(f"**Action:** {action}")
                    if project_id:
                        meta_items.append(f"**Project:** {project_id}")
                    if task_id:
                        meta_items.append(f"**Task:** {task_id}")
                    
                    if meta_items:
                        output.append("**Metadata:**")
                        for item in meta_items:
                            output.append(f"- {item}")
                        output.append("")
                
                output.append("---")
                output.append("")
            
            return "\n".join(output)
        
        except Exception as e:
            logger.error(f"Error exporting Markdown for user {self.user_id}: {e}")
            return f"# Error\n\nFailed to export: {str(e)}"
    
    def export_by_project(self, project_id: str, format: str = "json") -> str:
        """
        Export conversations filtered by project.
        
        Args:
            project_id: The project ID
            format: Export format ('json', 'csv', 'markdown')
            
        Returns:
            Formatted export string
        """
        try:
            # Query messages with matching project_id
            query = self.conversations_ref.where(
                "metadata.project_id", "==", project_id
            ).stream()
            
            messages = []
            for doc in query:
                msg = doc.to_dict()
                msg["id"] = doc.id
                messages.append(msg)
            
            # Sort by timestamp
            messages.sort(
                key=lambda x: x.get("timestamp", datetime.now()),
                reverse=False
            )
            
            if format == "json":
                return json.dumps({
                    "user_id": self.user_id,
                    "project_id": project_id,
                    "exported_at": datetime.now().isoformat(),
                    "message_count": len(messages),
                    "messages": messages,
                }, indent=2, default=str)
            
            elif format == "csv":
                output = StringIO()
                if messages:
                    fieldnames = ["timestamp", "user_message", "agent_response"]
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for msg in messages:
                        writer.writerow({
                            "timestamp": msg.get("timestamp", ""),
                            "user_message": msg.get("user_message", ""),
                            "agent_response": msg.get("agent_response", ""),
                        })
                
                return output.getvalue()
            
            elif format == "markdown":
                output = [
                    f"# Project Conversations: {project_id}",
                    f"**Exported:** {datetime.now().isoformat()}",
                    f"**Messages:** {len(messages)}",
                    ""
                ]
                
                for i, msg in enumerate(messages, 1):
                    output.append(f"## Turn {i}")
                    output.append(f"> **User:** {msg.get('user_message', '')}")
                    output.append(f"\n**Agent:** {msg.get('agent_response', '')}\n")
                    output.append("---\n")
                
                return "\n".join(output)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        except Exception as e:
            logger.error(f"Error exporting project {project_id}: {e}")
            return f"Error exporting project: {str(e)}"
    
    def export_by_task(self, task_id: str, format: str = "json") -> str:
        """
        Export conversations filtered by task.
        
        Args:
            task_id: The task ID
            format: Export format ('json', 'csv', 'markdown')
            
        Returns:
            Formatted export string
        """
        try:
            # Query messages with matching task_id
            query = self.conversations_ref.where(
                "metadata.task_id", "==", task_id
            ).stream()
            
            messages = []
            for doc in query:
                msg = doc.to_dict()
                msg["id"] = doc.id
                messages.append(msg)
            
            # Sort by timestamp
            messages.sort(
                key=lambda x: x.get("timestamp", datetime.now()),
                reverse=False
            )
            
            if format == "json":
                return json.dumps({
                    "user_id": self.user_id,
                    "task_id": task_id,
                    "exported_at": datetime.now().isoformat(),
                    "message_count": len(messages),
                    "messages": messages,
                }, indent=2, default=str)
            
            elif format == "csv":
                output = StringIO()
                if messages:
                    fieldnames = ["timestamp", "user_message", "agent_response"]
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for msg in messages:
                        writer.writerow({
                            "timestamp": msg.get("timestamp", ""),
                            "user_message": msg.get("user_message", ""),
                            "agent_response": msg.get("agent_response", ""),
                        })
                
                return output.getvalue()
            
            elif format == "markdown":
                output = [
                    f"# Task Conversations: {task_id}",
                    f"**Exported:** {datetime.now().isoformat()}",
                    f"**Messages:** {len(messages)}",
                    ""
                ]
                
                for i, msg in enumerate(messages, 1):
                    output.append(f"## Turn {i}")
                    output.append(f"> **User:** {msg.get('user_message', '')}")
                    output.append(f"\n**Agent:** {msg.get('agent_response', '')}\n")
                    output.append("---\n")
                
                return "\n".join(output)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        except Exception as e:
            logger.error(f"Error exporting task {task_id}: {e}")
            return f"Error exporting task: {str(e)}"
