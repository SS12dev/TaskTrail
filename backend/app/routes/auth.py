from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.models.auth import UserResponse, TokenVerifyResponse
from app.firebase import get_firestore_client
from firebase_admin import firestore
import logging
from typing import Dict, Any

# Create router for authentication-related endpoints
router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.get("/verify", response_model=TokenVerifyResponse)
async def verify_token(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Verify the Firebase ID token and sync user data to Firestore.

    This endpoint serves two purposes:
    1. Confirms that the provided token is valid
    2. Syncs user information to Firestore /users collection

    The frontend should call this endpoint after login to ensure
    the user document exists in Firestore and is up to date.

    Args:
        user: Current user from get_current_user dependency

    Returns:
        TokenVerifyResponse with validation status and user info
    """
    try:
        # Get Firestore client
        db = get_firestore_client()
        user_ref = db.collection("users").document(user["uid"])

        # Update or create user document in Firestore
        # merge=True ensures we don't overwrite existing data
        user_ref.set({
            "email": user["email"],
            "email_verified": user["email_verified"],
            "name": user.get("name"),
            "picture": user.get("picture"),
            "last_login": firestore.SERVER_TIMESTAMP,
        }, merge=True)

        logger.info(f"User {user['uid']} verified and synced to Firestore")

        return {
            "valid": True,
            "user": UserResponse(**user)
        }

    except Exception as e:
        logger.error(f"Error syncing user to Firestore: {e}")
        # Still return success if token is valid, even if Firestore sync fails
        # This prevents blocking the user if Firestore has issues
        return {
            "valid": True,
            "user": UserResponse(**user)
        }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user information.

    This is a simple protected endpoint that returns the current
    user's information extracted from their Firebase token.

    Args:
        user: Current user from get_current_user dependency

    Returns:
        UserResponse with current user information
    """
    return UserResponse(**user)
