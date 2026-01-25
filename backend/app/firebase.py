import firebase_admin
from firebase_admin import credentials, auth, firestore
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global flag to track initialization
_initialized = False


def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.

    This function should be called once during application startup.
    It sets up the Firebase Admin SDK for authentication and Firestore access.
    """
    global _initialized

    if _initialized:
        logger.info("Firebase Admin SDK already initialized")
        return

    try:
        cred = credentials.Certificate(settings.firebase_service_account_path)
        firebase_admin.initialize_app(cred)
        _initialized = True
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise


def get_auth_client():
    """
    Get the Firebase Auth client for user authentication operations.

    Returns:
        Firebase Auth module for verifying tokens and managing users
    """
    return auth


def get_firestore_client():
    """
    Get the Firestore database client.

    Returns:
        Firestore client for database operations
    """
    return firestore.client()
