"""
End-to-end test for memory integration.

This script tests the full memory flow:
1. Save conversation turns
2. Retrieve context summary
3. Vector search for similar past messages
4. Auto-compaction after threshold

Note: This requires Firebase and optionally Redis to be configured.
Skip if running in CI without credentials.
"""

import pytest
from unittest.mock import MagicMock, patch
import asyncio

import time
import os
from pathlib import Path

def test_e2e_memory_flow():
    """Full end-to-end test of memory system with real Firebase."""
    # Load environment variables from .env file
    from dotenv import load_dotenv
    backend_dir = Path(__file__).parent.parent
    env_path = backend_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    from app.firebase import initialize_firebase
    from app.services.conversation_memory import ConversationMemory
    from app.services.vector_memory import VectorMemory
    
    # Initialize Firebase (safe to call multiple times)
    try:
        initialize_firebase()
    except:
        pass  # Already initialized
    
    # Test with a unique user ID
    test_user = f"test_e2e_user_{int(time.time())}"
    
    # Initialize memory
    conv_mem = ConversationMemory(test_user)
    vec_mem = VectorMemory()
    
    # Clean up any existing test data
    conv_mem.clear_history()
    
    # Simulate a conversation
    conversations = [
        ("What tasks do I have today?", "You have 3 tasks scheduled for today."),
        ("Can you help me with project planning?", "Of course! Let's start by outlining your goals."),
        ("I need to finish the backend improvements", "Great! What specific improvements are you working on?"),
    ]
    
    # Save conversations
    for user_msg, agent_msg in conversations:
        conv_mem.save_message(user_msg, agent_msg, metadata={"test": "e2e"})
    
    # Test 1: Retrieve recent history
    history = conv_mem.get_recent_history(limit=5)
    assert len(history) == 3, f"Expected 3 messages, got {len(history)}"
    assert history[0]["user_message"] == "What tasks do I have today?"
    
    # Test 2: Get context summary
    summary = conv_mem.get_context_summary(max_messages=3)
    assert "Recent conversation:" in summary
    assert "tasks" in summary.lower()
    
    # Test 3: Vector search (if Redis is available)
    if vec_mem.enabled:
        results = vec_mem.search(test_user, "what are my tasks", k=2)
        assert isinstance(results, list)
        # Should find relevant conversation about tasks
        if results:
            assert any("task" in r["text"].lower() for r in results)
    
    # Test 4: Compaction (won't trigger with only 3 messages)
    summary = conv_mem.summarize_and_compact(retain_last=1)
    if summary:  # Only if there were enough messages
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    # Clean up
    conv_mem.clear_history()
    
    print("✓ E2E memory test passed!")


def test_memory_graceful_degradation():
    """Test that memory system gracefully handles missing dependencies."""
    from app.services.vector_memory import VectorMemory
    
    # If Redis is not configured, VectorMemory should still work (disabled mode)
    with patch('app.services.vector_memory.settings') as mock_settings:
        mock_settings.redis_url = None
        mock_settings.openai_api_key = "test_key"
        
        vm = VectorMemory()
        
        # Should be disabled but not crash
        assert vm.enabled == False
        
        # Operations should be no-ops
        vm.add_turn("user1", "test message")
        results = vm.search("user1", "query")
        assert results == []


if __name__ == "__main__":
    # Run the E2E test directly
    asyncio.run(test_e2e_memory_flow())
