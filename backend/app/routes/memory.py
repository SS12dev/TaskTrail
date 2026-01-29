"""
Memory Analytics API Routes.

Provides endpoints for memory insights, statistics, and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import verify_token
from app.services.memory_analytics import MemoryAnalytics
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/stats")
async def get_memory_stats(user_id: str = Depends(verify_token)) -> Dict[str, Any]:
    """
    Get comprehensive memory statistics for the authenticated user.
    
    Returns:
        - total messages and summaries
        - vector memory status
        - compaction recommendations
        - message trends (past week)
    """
    try:
        analytics = MemoryAnalytics(user_id)
        stats = analytics.get_memory_stats()
        
        if not stats:
            raise HTTPException(status_code=500, detail="Failed to retrieve memory stats")
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memory stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory stats")


@router.get("/timeline")
async def get_message_timeline(
    days: int = 30,
    user_id: str = Depends(verify_token)
) -> Dict[str, int]:
    """
    Get message count timeline for the past N days.
    
    Args:
        days: Number of days to analyze (default: 30, max: 365)
        
    Returns:
        Dict mapping dates (YYYY-MM-DD) to message counts
    """
    try:
        # Validate days parameter
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        analytics = MemoryAnalytics(user_id)
        timeline = analytics.get_message_timeline(days=days)
        
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving timeline for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve message timeline")


@router.get("/projects/{project_id}")
async def get_project_memory_stats(
    project_id: str,
    user_id: str = Depends(verify_token)
) -> Dict[str, Any]:
    """
    Get memory statistics for a specific project.
    
    Args:
        project_id: The project ID
        
    Returns:
        Project-specific memory stats including message count
    """
    try:
        analytics = MemoryAnalytics(user_id)
        stats = analytics.get_project_stats(project_id)
        
        return stats
    except Exception as e:
        logger.error(f"Error retrieving project stats for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project stats")


@router.get("/tasks/{task_id}")
async def get_task_memory_stats(
    task_id: str,
    user_id: str = Depends(verify_token)
) -> Dict[str, Any]:
    """
    Get memory statistics for a specific task.
    
    Args:
        task_id: The task ID
        
    Returns:
        Task-specific memory stats including message count
    """
    try:
        analytics = MemoryAnalytics(user_id)
        stats = analytics.get_task_stats(task_id)
        
        return stats
    except Exception as e:
        logger.error(f"Error retrieving task stats for {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task stats")


@router.get("/agents")
async def get_agent_distribution(user_id: str = Depends(verify_token)) -> Dict[str, int]:
    """
    Get message distribution by agent type.
    
    Shows which agents (planner, executor, query, conversation) 
    have been called most frequently.
    
    Returns:
        Dict mapping agent names to message counts
    """
    try:
        analytics = MemoryAnalytics(user_id)
        agent_stats = analytics.get_agent_stats()
        
        return agent_stats
    except Exception as e:
        logger.error(f"Error retrieving agent stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent statistics")


@router.get("/recent")
async def get_recent_messages(
    limit: int = 10,
    user_id: str = Depends(verify_token)
):
    """
    Get recent conversation messages.
    
    Args:
        limit: Number of messages to retrieve (default: 10, max: 100)
        
    Returns:
        List of recent messages with metadata
    """
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        analytics = MemoryAnalytics(user_id)
        messages = analytics.get_recent_messages(limit=limit)
        
        return {
            "user_id": user_id,
            "count": len(messages),
            "messages": messages,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recent messages for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent messages")


@router.get("/health")
async def memory_health_check(user_id: str = Depends(verify_token)) -> Dict[str, Any]:
    """
    Check the health of memory systems.
    
    Returns:
        Health status for conversation memory, vector memory, and compaction
    """
    try:
        analytics = MemoryAnalytics(user_id)
        stats = analytics.get_memory_stats()
        
        return {
            "status": "healthy" if stats.get("messages", {}).get("total", 0) > 0 else "no_data",
            "memory_available": True,
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"Error checking memory health for user {user_id}: {e}")
        return {
            "status": "error",
            "memory_available": False,
            "error": str(e),
        }
