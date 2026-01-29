"""
Enhancements for project and task-aware memory filtering.

This module provides utilities to filter conversation memory
by specific projects or tasks, enabling more contextual responses.
"""

from typing import List, Dict, Optional, Any
from app.models.project import Project
from app.models.task import Task
import logging

logger = logging.getLogger(__name__)


class ProjectTaskMemoryFilter:
    """Filters conversation history by projects and tasks."""
    
    @staticmethod
    def add_project_context(metadata: Dict[str, Any], project_id: str, project_name: str) -> Dict[str, Any]:
        """
        Add project context to conversation metadata.
        
        Args:
            metadata: Existing metadata dictionary
            project_id: The project ID
            project_name: The project name
            
        Returns:
            Updated metadata with project context
        """
        updated = metadata.copy() if metadata else {}
        updated["project_id"] = project_id
        updated["project_name"] = project_name
        return updated
    
    @staticmethod
    def add_task_context(
        metadata: Dict[str, Any], 
        task_id: str, 
        task_name: str, 
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add task context to conversation metadata.
        
        Args:
            metadata: Existing metadata dictionary
            task_id: The task ID
            task_name: The task name
            project_id: Optional project ID if task is in a project
            
        Returns:
            Updated metadata with task context
        """
        updated = metadata.copy() if metadata else {}
        updated["task_id"] = task_id
        updated["task_name"] = task_name
        if project_id:
            updated["project_id"] = project_id
        return updated
    
    @staticmethod
    def filter_by_project(
        conversations: List[Dict[str, Any]], 
        project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Filter conversation history to those related to a specific project.
        
        Args:
            conversations: List of conversation records
            project_id: The project ID to filter by
            
        Returns:
            Filtered list of conversations
        """
        return [
            conv for conv in conversations 
            if conv.get("metadata", {}).get("project_id") == project_id
        ]
    
    @staticmethod
    def filter_by_task(
        conversations: List[Dict[str, Any]], 
        task_id: str
    ) -> List[Dict[str, Any]]:
        """
        Filter conversation history to those related to a specific task.
        
        Args:
            conversations: List of conversation records
            task_id: The task ID to filter by
            
        Returns:
            Filtered list of conversations
        """
        return [
            conv for conv in conversations 
            if conv.get("metadata", {}).get("task_id") == task_id
        ]
    
    @staticmethod
    def filter_by_agent_type(
        conversations: List[Dict[str, Any]], 
        agent_type: str
    ) -> List[Dict[str, Any]]:
        """
        Filter conversation history by agent that processed it.
        
        Args:
            conversations: List of conversation records
            agent_type: The agent type (planner, executor, query, conversation)
            
        Returns:
            Filtered list of conversations
        """
        return [
            conv for conv in conversations
            if agent_type in conv.get("metadata", {}).get("agents_called", [])
        ]


def build_memory_context_for_task(
    task: Dict[str, Any],
    recent_history: List[Dict[str, Any]],
    vector_search_results: List[Dict[str, Any]] = None
) -> str:
    """
    Build contextual memory string for a specific task.
    
    Args:
        task: The task object
        recent_history: Recent conversation history
        vector_search_results: Results from vector search (optional)
        
    Returns:
        Formatted memory context string
    """
    context_parts = []
    
    # Add task context
    context_parts.append(f"Task: {task.get('name', 'Unknown')} (ID: {task.get('id', 'N/A')})")
    if task.get('description'):
        context_parts.append(f"Description: {task['description'][:200]}")
    if task.get('priority'):
        context_parts.append(f"Priority: {task['priority']}")
    
    # Filter history by this task
    task_history = ProjectTaskMemoryFilter.filter_by_task(
        recent_history,
        task.get('id', '')
    )
    
    if task_history:
        context_parts.append(f"\nRecent conversation about this task ({len(task_history)} messages):")
        for msg in task_history[:3]:  # Last 3 messages
            context_parts.append(f"- {msg.get('user_message', '')[:100]}")
    
    # Add vector search results if available
    if vector_search_results:
        context_parts.append("\nSimilar past interactions:")
        for result in vector_search_results[:2]:
            context_parts.append(f"- {result.get('text', '')[:150]}")
    
    return "\n".join(context_parts)


def build_memory_context_for_project(
    project: Dict[str, Any],
    recent_history: List[Dict[str, Any]],
    vector_search_results: List[Dict[str, Any]] = None
) -> str:
    """
    Build contextual memory string for a specific project.
    
    Args:
        project: The project object
        recent_history: Recent conversation history
        vector_search_results: Results from vector search (optional)
        
    Returns:
        Formatted memory context string
    """
    context_parts = []
    
    # Add project context
    context_parts.append(f"Project: {project.get('name', 'Unknown')} (ID: {project.get('id', 'N/A')})")
    if project.get('description'):
        context_parts.append(f"Description: {project['description'][:200]}")
    
    # Filter history by this project
    project_history = ProjectTaskMemoryFilter.filter_by_project(
        recent_history,
        project.get('id', '')
    )
    
    if project_history:
        context_parts.append(f"\nRecent conversation about this project ({len(project_history)} messages):")
        for msg in project_history[:3]:  # Last 3 messages
            context_parts.append(f"- {msg.get('user_message', '')[:100]}")
    
    # Add vector search results if available
    if vector_search_results:
        context_parts.append("\nSimilar past interactions:")
        for result in vector_search_results[:2]:
            context_parts.append(f"- {result.get('text', '')[:150]}")
    
    return "\n".join(context_parts)
