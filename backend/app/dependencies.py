from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Security scheme for Bearer token authentication
# This tells FastAPI to look for "Authorization: Bearer <token>" in request headers
security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to verify Firebase ID token from Authorization header.

    This is the core authentication dependency that should be used on all
    protected endpoints. It extracts the token from the Authorization header,
    verifies it with Firebase Admin SDK, and returns the decoded user information.

    Args:
        credentials: Bearer token automatically extracted from Authorization header

    Returns:
        Dict containing decoded token with user information including:
        - uid: User's unique Firebase ID
        - email: User's email address
        - email_verified: Whether email is verified
        - name: User's display name (if set)
        - picture: User's profile picture URL (if set)

    Raises:
        HTTPException: 401 if token is invalid, expired, or revoked

    Example usage in endpoint:
        @router.get("/protected")
        async def protected_route(user: Dict = Depends(get_current_user)):
            return {"message": f"Hello {user['email']}"}
    """
    token = credentials.credentials

    try:
        # Verify the ID token with Firebase Admin SDK
        # check_revoked=True ensures that revoked tokens are rejected
        decoded_token = auth.verify_id_token(token, check_revoked=True)

        logger.info(f"Token verified successfully for user: {decoded_token['uid']}")
        return decoded_token

    except auth.ExpiredIdTokenError:
        logger.warning("Expired token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please refresh your token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.RevokedIdTokenError:
        logger.warning("Revoked token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        logger.warning("Invalid token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Backward-compatible dependency for routes expecting verify_token to return UID
async def verify_token(
    token_data: Dict[str, Any] = Depends(verify_firebase_token)
) -> str:
    return token_data["uid"]


async def get_current_user(
    token_data: Dict[str, Any] = Depends(verify_firebase_token)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user information.

    This is a convenience wrapper around verify_firebase_token that
    extracts and returns only the user-relevant information.
    Use this dependency on protected endpoints to get the current user.

    Args:
        token_data: Decoded token from verify_firebase_token dependency

    Returns:
        Dict containing user information:
        - uid: User's unique ID
        - email: User's email
        - email_verified: Email verification status
        - name: Display name (optional)
        - picture: Profile picture URL (optional)
    """
    return {
        "uid": token_data["uid"],
        "email": token_data.get("email"),
        "email_verified": token_data.get("email_verified", False),
        "name": token_data.get("name"),
        "picture": token_data.get("picture"),
    }
