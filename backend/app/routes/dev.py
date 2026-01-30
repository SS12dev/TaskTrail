"""
Development utility routes for managing user data during development/testing.

These endpoints allow clearing user data from Firestore and Redis for fresh starts.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.dependencies import get_current_user
from app.firebase import get_firestore_client
import redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["development"])


@router.post("/clear-user-data")
async def clear_user_data(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear all user data (conversations, tasks, projects, cache).
    
    This endpoint deletes:
    - All conversations from Firestore
    - All tasks from Firestore
    - All projects from Firestore
    - All Redis cache entries
    
    WARNING: This is destructive and cannot be undone!
    Use only in development/testing.
    
    Returns:
        Summary of deleted items
    """
    user_id = current_user["uid"]
    logger.warning(f"User {user_id} is clearing all their data")
    
    db = get_firestore_client()
    results = {
        "conversations": 0,
        "tasks": 0,
        "projects": 0,
        "cache": 0,
    }
    
    try:
        # Clear conversations
        conversations_ref = (
            db.collection("users")
            .document(user_id)
            .collection("conversations")
        )
        for doc in conversations_ref.stream():
            doc.reference.delete()
            results["conversations"] += 1
        
        # Clear tasks
        tasks_ref = (
            db.collection("users")
            .document(user_id)
            .collection("tasks")
        )
        for doc in tasks_ref.stream():
            doc.reference.delete()
            results["tasks"] += 1
        
        # Clear projects
        projects_ref = (
            db.collection("users")
            .document(user_id)
            .collection("projects")
        )
        for doc in projects_ref.stream():
            doc.reference.delete()
            results["projects"] += 1
        
        # Clear Redis cache
        try:
            redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=1,  # Conversations
                decode_responses=True
            )
            redis_client.ping()
            
            # Clear all conversation cache for this user
            pattern = f"conv:{user_id}:*"
            keys = redis_client.keys(pattern)
            for key in keys:
                redis_client.delete(key)
                results["cache"] += 1
        except Exception as e:
            logger.warning(f"Redis cache clear skipped: {e}")
        
        logger.info(f"Cleared data for user {user_id}: {results}")
        
        return {
            "success": True,
            "message": "All user data cleared successfully",
            "deleted": results
        }
    
    except Exception as e:
        logger.error(f"Error clearing user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear user data: {str(e)}"
        )


@router.post("/verify-user-isolation")
async def verify_user_isolation(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify that data is properly isolated by user.
    
    This endpoint checks that:
    - All conversations belong to current user
    - All tasks belong to current user
    - All projects belong to current user
    - Redis cache keys use user_id
    
    Returns:
        Verification results
    """
    user_id = current_user["uid"]
    db = get_firestore_client()
    
    results = {
        "user_id": user_id,
        "conversations": {
            "total": 0,
            "isolated": True,
            "issues": []
        },
        "tasks": {
            "total": 0,
            "isolated": True,
            "issues": []
        },
        "projects": {
            "total": 0,
            "isolated": True,
            "issues": []
        },
        "cache": {
            "total": 0,
            "isolated": True,
            "issues": []
        }
    }
    
    try:
        # Check conversations
        conversations_ref = (
            db.collection("users")
            .document(user_id)
            .collection("conversations")
        )
        for doc in conversations_ref.stream():
            results["conversations"]["total"] += 1
            doc_data = doc.to_dict()
            if doc_data.get("user_id") != user_id:
                results["conversations"]["isolated"] = False
                results["conversations"]["issues"].append(
                    f"Conversation {doc.id} has user_id {doc_data.get('user_id')}"
                )
        
        # Check tasks
        tasks_ref = (
            db.collection("users")
            .document(user_id)
            .collection("tasks")
        )
        for doc in tasks_ref.stream():
            results["tasks"]["total"] += 1
            doc_data = doc.to_dict()
            if doc_data.get("user_id") != user_id:
                results["tasks"]["isolated"] = False
                results["tasks"]["issues"].append(
                    f"Task {doc.id} has user_id {doc_data.get('user_id')}"
                )
        
        # Check projects
        projects_ref = (
            db.collection("users")
            .document(user_id)
            .collection("projects")
        )
        for doc in projects_ref.stream():
            results["projects"]["total"] += 1
            doc_data = doc.to_dict()
            if doc_data.get("user_id") != user_id:
                results["projects"]["isolated"] = False
                results["projects"]["issues"].append(
                    f"Project {doc.id} has user_id {doc_data.get('user_id')}"
                )
        
        # Check Redis cache
        try:
            redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=1,
                decode_responses=True
            )
            redis_client.ping()
            
            # Check conversation cache keys
            all_pattern = "conv:*:*"
            all_keys = redis_client.keys(all_pattern)
            user_keys = [k for k in all_keys if k.startswith(f"conv:{user_id}:")]
            
            results["cache"]["total"] = len(all_keys)
            for key in all_keys:
                if not key.startswith(f"conv:{user_id}:"):
                    results["cache"]["isolated"] = False
                    results["cache"]["issues"].append(
                        f"Cache key '{key}' belongs to different user"
                    )
        except Exception as e:
            logger.warning(f"Redis check skipped: {e}")
        
        # Determine overall status
        all_isolated = (
            results["conversations"]["isolated"] and
            results["tasks"]["isolated"] and
            results["projects"]["isolated"] and
            results["cache"]["isolated"]
        )
        
        return {
            "success": True,
            "user_isolated": all_isolated,
            "verification": results
        }
    
    except Exception as e:
        logger.error(f"Error verifying user isolation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )
