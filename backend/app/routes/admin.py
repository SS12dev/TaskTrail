"""
Admin API routes for user management, analytics, and configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.dependencies_admin import (
    verify_admin_token,
    require_super_admin,
    Permissions,
    check_permission
)
from app.models.admin import (
    UserSummary,
    UserDetail,
    UserListResponse,
    UserUpdateRequest,
    TokenUsageResponse,
    SystemOverview,
    AnalyticsResponse,
    UserRanking,
    SystemConfig,
    ConfigUpdateRequest,
    AuditLog,
    AuditLogListResponse,
    AdminActionResponse
)
from app.firebase import get_firestore_client
from app.services.token_tracker import get_token_tracker
from firebase_admin import firestore, auth as firebase_auth
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


# ============================================================================
# Audit Logging Helper
# ============================================================================

async def log_admin_action(
    admin_id: str,
    admin_email: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict] = None,
    success: bool = True
):
    """Log admin action to audit trail."""
    try:
        db = get_firestore_client()
        log_ref = db.collection("admin_audit_log").document()
        
        log_ref.set({
            "admin_id": admin_id,
            "admin_email": admin_email,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "details": details or {},
            "success": success
        })
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")


# ============================================================================
# User Management Endpoints
# ============================================================================

@router.get("/users", response_model=UserListResponse)
async def list_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by email"),
    tier: Optional[str] = Query(None, description="Filter by tier"),
    suspended: Optional[bool] = Query(None, description="Filter by suspension status"),
    admin: Dict[str, Any] = Depends(verify_admin_token)
):
    """
    List all users with pagination and filtering.
    
    Requires: view_users permission
    """
    try:
        db = get_firestore_client()
        tracker = get_token_tracker()
        
        # Start with all users query
        query = db.collection("users")
        
        # Apply filters
        if tier:
            query = query.where(filter=firestore.FieldFilter("current_tier", "==", tier))
        
        if suspended is not None:
            query = query.where(filter=firestore.FieldFilter("is_suspended", "==", suspended))
        
        # Get total count (for pagination)
        all_docs = list(query.stream())
        
        # Apply search filter (client-side due to Firestore limitations)
        if search:
            all_docs = [
                doc for doc in all_docs
                if search.lower() in doc.to_dict().get("email", "").lower()
            ]
        
        total = len(all_docs)
        
        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_docs = all_docs[start_idx:end_idx]
        
        # Build user summaries
        users = []
        for doc in page_docs:
            user_data = doc.to_dict()
            user_id = doc.id
            
            # Get token usage (last 30 days)
            usage = tracker.get_user_usage(user_id, days=30)
            
            # Count tasks and projects
            tasks_count = len(list(
                db.collection("tasks")
                .where(filter=firestore.FieldFilter("userId", "==", user_id))
                .limit(1000)
                .stream()
            ))
            
            projects_count = len(list(
                db.collection("users")
                .document(user_id)
                .collection("projects")
                .limit(1000)
                .stream()
            ))
            
            users.append(UserSummary(
                uid=user_id,
                email=user_data.get("email"),
                display_name=user_data.get("name"),
                created_at=user_data.get("created_at", datetime.utcnow()),
                last_login=user_data.get("last_login"),
                task_count=tasks_count,
                project_count=projects_count,
                total_tokens_used=usage["total_tokens"],
                current_tier=user_data.get("current_tier", "free"),
                is_suspended=user_data.get("is_suspended", False)
            ))
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "list_users",
            "users",
            details={"page": page, "page_size": page_size, "filters": {
                "search": search, "tier": tier, "suspended": suspended
            }}
        )
        
        return UserListResponse(
            users=users,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end_idx < total
        )
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user_detail(
    user_id: str,
    admin: Dict[str, Any] = Depends(verify_admin_token)
):
    """
    Get detailed information about a specific user.
    
    Requires: view_users permission
    """
    try:
        db = get_firestore_client()
        tracker = get_token_tracker()
        
        # Get user from Firestore
        user_doc = db.collection("users").document(user_id).get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = user_doc.to_dict()
        
        # Get Firebase auth record for additional details
        try:
            firebase_user = firebase_auth.get_user(user_id)
            email_verified = firebase_user.email_verified
            photo_url = firebase_user.photo_url
        except:
            email_verified = False
            photo_url = None
        
        # Get usage stats
        usage = tracker.get_user_usage(user_id, days=30)
        limit_status = tracker.check_user_limit(
            user_id, 
            user_data.get("current_tier", "free")
        )
        
        # Count tasks and projects
        tasks_count = len(list(
            db.collection("tasks")
            .where(filter=firestore.FieldFilter("userId", "==", user_id))
            .limit(1000)
            .stream()
        ))
        
        projects_count = len(list(
            db.collection("users")
            .document(user_id)
            .collection("projects")
            .limit(1000)
            .stream()
        ))
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "view_user_detail",
            "user",
            resource_id=user_id
        )
        
        return UserDetail(
            uid=user_id,
            email=user_data.get("email"),
            display_name=user_data.get("name"),
            email_verified=email_verified,
            photo_url=photo_url,
            created_at=user_data.get("created_at", datetime.utcnow()),
            last_login=user_data.get("last_login"),
            task_count=tasks_count,
            project_count=projects_count,
            total_tokens_used=usage["total_tokens"],
            current_tier=user_data.get("current_tier", "free"),
            is_suspended=user_data.get("is_suspended", False),
            metadata=user_data.get("metadata", {}),
            usage_stats={
                "last_30_days": usage,
                "limit_status": limit_status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user detail: {str(e)}"
        )


@router.get("/users/{user_id}/usage", response_model=TokenUsageResponse)
async def get_user_token_usage(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    admin: Dict[str, Any] = Depends(verify_admin_token)
):
    """
    Get detailed token usage for a user.
    
    Requires: view_users permission
    """
    try:
        tracker = get_token_tracker()
        usage = tracker.get_user_usage(user_id, days=days)
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "view_user_usage",
            "user",
            resource_id=user_id,
            details={"days": days}
        )
        
        return TokenUsageResponse(**usage)
        
    except Exception as e:
        logger.error(f"Error getting user usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user usage: {str(e)}"
        )


@router.patch("/users/{user_id}", response_model=AdminActionResponse)
async def update_user(
    user_id: str,
    update: UserUpdateRequest,
    admin: Dict[str, Any] = Depends(verify_admin_token)
):
    """
    Update user properties.
    
    Requires: edit_users permission
    """
    try:
        db = get_firestore_client()
        user_ref = db.collection("users").document(user_id)
        
        # Check if user exists
        if not user_ref.get().exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Build update dict
        update_dict = {}
        if update.is_suspended is not None:
            update_dict["is_suspended"] = update.is_suspended
        if update.current_tier is not None:
            update_dict["current_tier"] = update.current_tier
        if update.notes is not None:
            update_dict["admin_notes"] = update.notes
        
        update_dict["updated_at"] = firestore.SERVER_TIMESTAMP
        update_dict[f"updated_by_admin"] = admin["uid"]
        
        # Update user
        user_ref.update(update_dict)
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "update_user",
            "user",
            resource_id=user_id,
            details=update_dict
        )
        
        return AdminActionResponse(
            success=True,
            message=f"User {user_id} updated successfully",
            data=update_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "update_user",
            "user",
            resource_id=user_id,
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=AdminActionResponse)
async def delete_user(
    user_id: str,
    admin: Dict[str, Any] = Depends(require_super_admin)
):
    """
    Delete a user and all their data.
    
    Requires: super_admin role
    WARNING: This is irreversible!
    """
    try:
        db = get_firestore_client()
        
        # Delete user from Firebase Auth
        try:
            firebase_auth.delete_user(user_id)
        except Exception as e:
            logger.warning(f"Failed to delete Firebase auth user: {e}")
        
        # Delete user document
        db.collection("users").document(user_id).delete()
        
        # Delete user's tasks
        tasks = db.collection("tasks").where(
            filter=firestore.FieldFilter("userId", "==", user_id)
        ).stream()
        for task in tasks:
            task.reference.delete()
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "delete_user",
            "user",
            resource_id=user_id
        )
        
        return AdminActionResponse(
            success=True,
            message=f"User {user_id} and all associated data deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "delete_user",
            "user",
            resource_id=user_id,
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get("/analytics/overview", response_model=SystemOverview)
async def get_system_overview(
    admin: Dict[str, Any] = Depends(verify_admin_token)
):
    """
    Get high-level system statistics.
    
    Requires: view_analytics permission
    """
    try:
        db = get_firestore_client()
        tracker = get_token_tracker()
        
        # Count total users
        all_users = list(db.collection("users").stream())
        total_users = len(all_users)
        
        # Count active users (last 7 and 30 days)
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        active_7d = sum(
            1 for user in all_users
            if user.to_dict().get("last_activity", datetime.min) > seven_days_ago
        )
        
        active_30d = sum(
            1 for user in all_users
            if user.to_dict().get("last_activity", datetime.min) > thirty_days_ago
        )
        
        # Count tasks and projects
        total_tasks = len(list(db.collection("tasks").limit(10000).stream()))
        
        total_projects = 0
        total_conversations = 0
        for user in all_users:
            user_id = user.id
            projects = list(
                db.collection("users")
                .document(user_id)
                .collection("projects")
                .limit(1000)
                .stream()
            )
            total_projects += len(projects)
            
            conversations = list(
                db.collection("users")
                .document(user_id)
                .collection("conversations")
                .limit(1000)
                .stream()
            )
            total_conversations += len(conversations)
        
        # Get token usage
        usage_month = tracker.get_system_usage(days=30)
        usage_today = tracker.get_system_usage(days=1)
        
        avg_tokens_per_user = (
            usage_month["total_tokens"] / total_users if total_users > 0 else 0
        )
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "view_overview",
            "analytics"
        )
        
        return SystemOverview(
            total_users=total_users,
            active_users_7d=active_7d,
            active_users_30d=active_30d,
            total_tasks=total_tasks,
            total_projects=total_projects,
            total_conversations=total_conversations,
            tokens_today=usage_today["total_tokens"],
            tokens_this_month=usage_month["total_tokens"],
            cost_this_month=usage_month["total_cost"],
            avg_tokens_per_user=avg_tokens_per_user
        )
        
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system overview: {str(e)}"
        )


@router.get("/analytics/top-users")
async def get_top_users_by_usage(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    admin: Dict[str, Any] = Depends(verify_admin_token)
):
    """
    Get top users by token consumption.
    
    Requires: view_analytics permission
    """
    try:
        tracker = get_token_tracker()
        top_users = tracker.get_top_users(days=days, limit=limit)
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "view_top_users",
            "analytics",
            details={"days": days, "limit": limit}
        )
        
        return {
            "top_users": top_users,
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Error getting top users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top users: {str(e)}"
        )


# ============================================================================
# Configuration Management
# ============================================================================

@router.get("/config", response_model=SystemConfig)
async def get_system_config(
    admin: Dict[str, Any] = Depends(verify_admin_token)
):
    """
    Get current system configuration.
    
    Requires: view_config permission
    """
    try:
        db = get_firestore_client()
        config_doc = db.collection("system_config").document("current").get()
        
        if not config_doc.exists:
            # Return default config
            from app.config import settings
            return SystemConfig(
                openai={
                    "api_key": "***hidden***",  # Never expose full key
                    "default_model": settings.openai_model,
                    "temperature": settings.openai_temperature,
                    "max_tokens": settings.openai_max_tokens
                },
                tiers={},
                maintenance_mode=False,
                feature_flags={}
            )
        
        config_data = config_doc.to_dict()
        
        # Mask API key
        if "openai" in config_data and "api_key" in config_data["openai"]:
            key = config_data["openai"]["api_key"]
            config_data["openai"]["api_key"] = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***hidden***"
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "view_config",
            "config"
        )
        
        return SystemConfig(**config_data)
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}"
        )


@router.patch("/config", response_model=AdminActionResponse)
async def update_system_config(
    update: ConfigUpdateRequest,
    admin: Dict[str, Any] = Depends(require_super_admin)
):
    """
    Update system configuration.
    
    Requires: super_admin role
    """
    try:
        db = get_firestore_client()
        config_ref = db.collection("system_config").document("current")
        
        update_dict = {}
        
        if update.openai:
            update_dict["openai"] = update.openai.model_dump()
        if update.tiers:
            update_dict["tiers"] = {
                name: tier.model_dump() for name, tier in update.tiers.items()
            }
        if update.maintenance_mode is not None:
            update_dict["maintenance_mode"] = update.maintenance_mode
        if update.feature_flags:
            update_dict["feature_flags"] = update.feature_flags
        
        update_dict["updated_at"] = firestore.SERVER_TIMESTAMP
        update_dict["updated_by"] = admin["uid"]
        
        config_ref.set(update_dict, merge=True)
        
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "update_config",
            "config",
            details={"fields_updated": list(update_dict.keys())}
        )
        
        return AdminActionResponse(
            success=True,
            message="Configuration updated successfully",
            data=update_dict
        )
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        await log_admin_action(
            admin["uid"],
            admin["email"],
            "update_config",
            "config",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config: {str(e)}"
        )


# ============================================================================
# Audit Logs
# ============================================================================

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    admin: Dict[str, Any] = Depends(verify_admin_token)
):
    """
    Get audit logs with pagination and filtering.
    
    Requires: view_audit_logs permission
    """
    try:
        db = get_firestore_client()
        
        # Build query
        query = db.collection("admin_audit_log").order_by(
            "timestamp", direction=firestore.Query.DESCENDING
        )
        
        if action:
            query = query.where(filter=firestore.FieldFilter("action", "==", action))
        if resource_type:
            query = query.where(filter=firestore.FieldFilter("resource_type", "==", resource_type))
        
        # Get all matching documents (Firestore doesn't support offset well)
        all_docs = list(query.limit(page * page_size).stream())
        total = len(all_docs)
        
        # Paginate
        start_idx = (page - 1) * page_size
        page_docs = all_docs[start_idx:]
        
        logs = []
        for doc in page_docs:
            log_data = doc.to_dict()
            logs.append(AuditLog(
                id=doc.id,
                **log_data
            ))
        
        return AuditLogListResponse(
            logs=logs,
            total=total,
            page=page,
            page_size=page_size,
            has_next=len(all_docs) >= page * page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )
