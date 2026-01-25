"""
User Preferences Service for LangGraph Multi-Agent System.

This service manages user preferences in Firestore, allowing personalization
of the agent's behavior and responses.
"""

from google.cloud import firestore
from typing import Dict, Any, Optional
from app.firebase import get_firestore_client
import logging

logger = logging.getLogger(__name__)
from datetime import datetime
from app.models.user_context import UserContext
import pytz


class UserPreferences:
    """Manages user preferences in Firestore."""

    def __init__(self, user_id: str):
        """
        Initialize user preferences for a specific user.

        Args:
            user_id: The user's Firebase UID
        """
        self.user_id = user_id
        self.db = get_firestore_client()
        self.doc_ref = self.db.collection("user_preferences").document(user_id)

    def get_preferences(self) -> dict:
        """
        Get user preferences or return defaults.

        Returns:
            Dictionary of user preferences
        """
        try:
            doc = self.doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return self._default_preferences()
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {str(e)}")
            return self._default_preferences()

    def update_preference(self, key: str, value: Any) -> None:
        """
        Update a single user preference.

        Args:
            key: Preference key
            value: Preference value
        """
        try:
            self.doc_ref.set({key: value}, merge=True)
            logger.info(f"Updated preference {key} for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error updating preference: {str(e)}")

    def update_preferences(self, prefs: dict) -> None:
        """
        Update multiple user preferences.

        Args:
            prefs: Dictionary of preferences to update
        """
        try:
            self.doc_ref.set(prefs, merge=True)
            logger.info(f"Updated preferences for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")

    def _default_preferences(self) -> dict:
        """
        Get default preferences for new users.

        Returns:
            Dictionary of default preferences
        """
        return {
            "default_priority": "medium",
            "preferred_due_date": "tomorrow",
            "work_hours": {"start": 9, "end": 17},
            "communication_style": "professional",
            "enable_suggestions": True,
            "timezone": "UTC"
        }
    
        async def get_user_context(self) -> UserContext:
            """
            Build UserContext for the user with their timezone and current time.
        
            Returns:
                UserContext instance with user's timezone information
            """
            try:
                prefs = self.get_preferences()
                timezone = prefs.get("timezone", "UTC")
                locale = prefs.get("locale", "en_US")
                country = prefs.get("country")
            
                # Create context with user's timezone
                context = UserContext.from_timezone(timezone=timezone)
                context.locale = locale
                if country:
                    context.country = country
            
                logger.debug(f"Built user context for {self.user_id}: {timezone}")
                return context
            
            except Exception as e:
                logger.error(f"Error building user context for {self.user_id}: {str(e)}")
                # Return default context if error occurs
                return UserContext.from_timezone()
