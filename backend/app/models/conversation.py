"""
Conversation models for AI Agent chat persistence.
"""

from typing import List, Optional, TypedDict
from datetime import datetime


class ConversationMessage(TypedDict):
    """Individual message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime


class Conversation(TypedDict, total=False):
    """Conversation document structure for Firestore."""
    id: str  # Unique conversation ID
    user_id: str  # Firebase UID
    title: str  # Auto-generated or user-set title
    messages: List[ConversationMessage]  # Chat history
    created_at: datetime
    updated_at: datetime
    archived: bool  # Soft delete
    metadata: dict  # Task IDs created, agents used, etc.
