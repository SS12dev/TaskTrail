from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from typing import Dict, Any

# Create router with prefix and tags for API documentation
router = APIRouter(prefix="/test", tags=["Testing"])


@router.get("/public")
async def public_endpoint():
    """
    Public endpoint - no authentication required.

    Use this to test that the backend is running and accessible.

    Returns:
        Dict with success message
    """
    return {
        "message": "This is a public endpoint",
        "status": "success",
        "info": "No authentication required"
    }


@router.get("/protected")
async def protected_endpoint(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Protected endpoint - requires valid Firebase authentication token.

    This endpoint demonstrates how to protect routes using the
    get_current_user dependency. The user parameter will automatically
    contain the authenticated user's information.

    Args:
        user: Current user info from get_current_user dependency

    Returns:
        Dict with personalized message and user ID
    """
    return {
        "message": f"Hello {user.get('email', 'User')}!",
        "user_id": user["uid"],
        "status": "success",
        "info": "This is a protected endpoint"
    }
