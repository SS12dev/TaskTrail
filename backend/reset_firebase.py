#!/usr/bin/env python3
"""
Firebase Reset Script

This script completely clears your Firebase project:
- Deletes all documents in all Firestore collections
- Deletes all users from Firebase Authentication
- Useful for clean testing and resetting the development environment

⚠️ WARNING: This will permanently delete all data!
Use only for development/testing environments.

Usage:
    python reset_firebase.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.firebase import get_firestore_client, get_auth_client, initialize_firebase
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FirebaseReset:
    """Handles complete Firebase project reset."""

    def __init__(self):
        """Initialize Firebase clients."""
        # Initialize Firebase Admin SDK
        initialize_firebase()
        
        self.db = get_firestore_client()
        self.auth = get_auth_client()

    def delete_collection(self, collection_path: str, batch_size: int = 100) -> int:
        """
        Delete all documents in a collection.

        Args:
            collection_path: Path to collection (e.g., "users" or "users/uid/conversations")
            batch_size: Number of documents to delete per batch

        Returns:
            Number of documents deleted
        """
        try:
            docs = self.db.collection(collection_path).limit(batch_size).stream()
            
            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            # Recursively delete if there are more documents
            if deleted_count >= batch_size:
                return deleted_count + self.delete_collection(collection_path, batch_size)
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting collection {collection_path}: {e}")
            return 0

    def delete_user_subcollections(self, user_id: str) -> None:
        """
        Delete all subcollections under a user document.

        Args:
            user_id: Firebase user ID
        """
        subcollections = [
            "conversations",
            "tasks",
            "projects",
            "settings",
            "preferences"
        ]
        
        for subcol in subcollections:
            path = f"users/{user_id}/{subcol}"
            count = self.delete_collection(path)
            if count > 0:
                logger.info(f"  Deleted {count} documents from {subcol}")

    def reset_firestore(self) -> None:
        """Delete all documents in all collections."""
        logger.info("=" * 60)
        logger.info("CLEARING FIRESTORE DATABASE")
        logger.info("=" * 60)
        
        collections = [
            "users",
            "tasks",
            "projects",
            "conversations",
            "memory"
        ]
        
        # First delete all user subcollections
        logger.info("\n📂 Deleting user subcollections...")
        try:
            users = self.db.collection("users").stream()
            for user_doc in users:
                user_id = user_doc.id
                logger.info(f"  Cleaning up user: {user_id}")
                self.delete_user_subcollections(user_id)
        except Exception as e:
            logger.error(f"Error deleting user subcollections: {e}")
        
        # Delete root collections
        logger.info("\n📋 Deleting root collections...")
        for collection in collections:
            logger.info(f"  Deleting '{collection}' collection...")
            count = self.delete_collection(collection)
            logger.info(f"    ✓ Deleted {count} documents")

    def reset_authentication(self) -> None:
        """Delete all users from Firebase Authentication."""
        logger.info("\n" + "=" * 60)
        logger.info("CLEARING FIREBASE AUTHENTICATION")
        logger.info("=" * 60)
        
        try:
            # Get all users in batches
            page = self.auth.list_users()
            total_deleted = 0
            
            while page:
                for user in page.users:
                    try:
                        self.auth.delete_user(user.uid)
                        total_deleted += 1
                        logger.info(f"  ✓ Deleted user: {user.email or user.uid}")
                    except Exception as e:
                        logger.error(f"    ✗ Error deleting user {user.uid}: {e}")
                
                # Get next page
                page = page.get_next_page()
            
            logger.info(f"\n✓ Total users deleted: {total_deleted}")
        except Exception as e:
            logger.error(f"Error resetting authentication: {e}")

    def reset_all(self) -> None:
        """Execute complete reset."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"\n🔄 FIREBASE RESET INITIATED AT {timestamp}")
        logger.info("⚠️  This will permanently delete ALL data!\n")
        
        # Ask for confirmation
        response = input("Are you sure you want to reset Firebase? (type 'yes' to confirm): ").strip()
        if response.lower() != 'yes':
            logger.info("❌ Reset cancelled.")
            return
        
        response = input("Type 'DELETE ALL' to confirm permanent deletion: ").strip()
        if response != 'DELETE ALL':
            logger.info("❌ Reset cancelled.")
            return
        
        try:
            # Reset Firestore
            self.reset_firestore()
            
            # Reset Authentication
            self.reset_authentication()
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ FIREBASE RESET COMPLETE")
            logger.info("=" * 60)
            logger.info("Your Firebase project is now clean!")
            logger.info("Ready for fresh testing.\n")
            
        except Exception as e:
            logger.error(f"\n❌ Reset failed: {e}")
            sys.exit(1)


def main():
    """Run the Firebase reset."""
    try:
        reset = FirebaseReset()
        reset.reset_all()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
