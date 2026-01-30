"""
Admin authentication and authorization middleware.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, firestore
from app.firebase import get_firestore_client
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Verify Firebase token and check if user is an admin.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        Dict with admin user information

    Raises:
        HTTPException: 401 if token invalid, 403 if not an admin
    """
    token = credentials.credentials

    try:
        # Verify Firebase token
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        user_id = decoded_token["uid"]

        # Check if user is an admin
        db = get_firestore_client()
        admin_doc = db.collection("admins").document(user_id).get()

        if not admin_doc.exists:
            logger.warning(f"Non-admin user attempted admin access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )

        admin_data = admin_doc.to_dict()

        # Check if admin is active
        if not admin_data.get("is_active", True):
            logger.warning(f"Inactive admin attempted access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account is inactive."
            )

        # Update last login
        admin_doc.reference.update({
            "last_login": firestore.SERVER_TIMESTAMP
        })

        # Combine token data with admin data
        admin_info = {
            "uid": user_id,
            "email": decoded_token.get("email"),
            "role": admin_data.get("role", "admin"),
            "permissions": admin_data.get("permissions", []),
            "display_name": admin_data.get("display_name"),
        }

        logger.info(f"Admin authenticated: {user_id} ({admin_info['role']})")
        return admin_info

    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_super_admin(
    admin: Dict[str, Any] = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """
    Require super admin role.

    Args:
        admin: Admin info from verify_admin_token

    Returns:
        Admin info

    Raises:
        HTTPException: 403 if not super admin
    """
    if admin["role"] != "super_admin":
        logger.warning(
            f"Admin {admin['uid']} attempted super admin action "
            f"with role {admin['role']}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required."
        )

    return admin


async def check_permission(
    permission: str,
    admin: Dict[str, Any] = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """
    Check if admin has a specific permission.

    Args:
        permission: Permission to check
        admin: Admin info from verify_admin_token

    Returns:
        Admin info

    Raises:
        HTTPException: 403 if permission denied
    """
    # Super admins have all permissions
    if admin["role"] == "super_admin":
        return admin

    # Check if permission is granted
    if permission not in admin.get("permissions", []):
        logger.warning(
            f"Admin {admin['uid']} lacks permission: {permission}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission}"
        )

    return admin


# Permission definitions
class Permissions:
    """Standard permission definitions."""

    # User management
    VIEW_USERS = "view_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    SUSPEND_USERS = "suspend_users"

    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"

    # Configuration
    VIEW_CONFIG = "view_config"
    EDIT_CONFIG = "edit_config"
    MANAGE_API_KEYS = "manage_api_keys"

    # System
    VIEW_AUDIT_LOGS = "view_audit_logs"
    SYSTEM_MAINTENANCE = "system_maintenance"


# Role definitions with default permissions
ROLE_PERMISSIONS = {
    "super_admin": [
        # Super admin has all permissions
        Permissions.VIEW_USERS,
        Permissions.EDIT_USERS,
        Permissions.DELETE_USERS,
        Permissions.SUSPEND_USERS,
        Permissions.VIEW_ANALYTICS,
        Permissions.EXPORT_DATA,
        Permissions.VIEW_CONFIG,
        Permissions.EDIT_CONFIG,
        Permissions.MANAGE_API_KEYS,
        Permissions.VIEW_AUDIT_LOGS,
        Permissions.SYSTEM_MAINTENANCE,
    ],
    "admin": [
        # Regular admin - user management and analytics
        Permissions.VIEW_USERS,
        Permissions.EDIT_USERS,
        Permissions.SUSPEND_USERS,
        Permissions.VIEW_ANALYTICS,
        Permissions.VIEW_CONFIG,
        Permissions.VIEW_AUDIT_LOGS,
    ],
    "support": [
        # Support - read-only access
        Permissions.VIEW_USERS,
        Permissions.VIEW_ANALYTICS,
        Permissions.VIEW_CONFIG,
    ],
}


def get_role_permissions(role: str) -> List[str]:
    """Get default permissions for a role."""
    return ROLE_PERMISSIONS.get(role, [])
