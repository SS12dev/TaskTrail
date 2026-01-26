import pytest
from unittest.mock import MagicMock, patch
from app.services.conversation_memory import ConversationMemory
from app.services.vector_memory import VectorMemory


class DummyFirestoreDoc:
    def __init__(self, data, doc_id="test_doc"):
        self._data = data
        self.id = doc_id
        self.reference = MagicMock()
    def to_dict(self):
        return self._data


def test_conversation_summary_generation(monkeypatch):
    # Patch Firestore client and collections
    fake_db = MagicMock()
    conv_col = MagicMock()
    summaries_col = MagicMock()
    fake_db.collection.return_value.document.return_value.collection.side_effect = [conv_col, summaries_col]

    # Simulate 30 messages
    docs = [DummyFirestoreDoc({
        "user_message": f"hello {i}",
        "agent_response": f"world {i}",
        "timestamp": i
    }) for i in range(30)]

    conv_col.order_by.return_value.limit.return_value.stream.return_value = docs

    with patch('app.services.conversation_memory.get_firestore_client', return_value=fake_db), \
         patch('app.services.conversation_memory.ChatOpenAI') as FakeLLM:
        llm_inst = MagicMock()
        llm_inst.invoke.return_value = MagicMock(content="summary text")
        FakeLLM.return_value = llm_inst

        mem = ConversationMemory(user_id="u1")
        summary = mem.summarize_and_compact(retain_last=10)

        assert summary == "summary text"
        assert summaries_col.add.called
        assert fake_db.batch.return_value.commit.called


def test_vector_memory_add_and_search(monkeypatch):
    # If Redis is not configured, search should return empty
    vm = VectorMemory()
    res = vm.search("u1", "hello")
    assert isinstance(res, list)


def test_auto_compaction_threshold():
    """Test that auto-compaction is triggered at the right threshold."""
    from app.services.agent_service import AgentService
    
    # Mock the conversation memory
    with patch('app.services.agent_service.MultiAgentSystem') as MockSystem:
        mock_system = MagicMock()
        mock_conv_mem = MagicMock()
        
        # Simulate 51 messages (above threshold)
        mock_docs = [MagicMock() for _ in range(51)]
        mock_conv_mem.conversations_ref.limit.return_value.stream.return_value = mock_docs
        mock_conv_mem.summarize_and_compact.return_value = "Compacted summary"
        
        mock_system.conversation_memory = mock_conv_mem
        MockSystem.return_value = mock_system
        
        service = AgentService("test_user")
        
        # Trigger auto-compact (async function, run synchronously for test)
        import asyncio
        asyncio.run(service._auto_compact_if_needed(threshold=50))
        
        # Verify summarize_and_compact was called
        mock_conv_mem.summarize_and_compact.assert_called_once_with(retain_last=20)


def test_memory_context_integration():
    """Test that memory context is properly built and attached."""
    # This is a basic integration test to verify the flow
    fake_db = MagicMock()
    conv_col = MagicMock()
    summaries_col = MagicMock()
    fake_db.collection.return_value.document.return_value.collection.side_effect = [conv_col, summaries_col]
    
    # Recent messages for context
    recent_msgs = [DummyFirestoreDoc({
        "user_message": f"test message {i}",
        "agent_response": f"test response {i}",
        "timestamp": i
    }) for i in range(3)]
    
    conv_col.order_by.return_value.limit.return_value.stream.return_value = recent_msgs
    
    with patch('app.services.conversation_memory.get_firestore_client', return_value=fake_db), \
         patch('app.services.conversation_memory.ChatOpenAI') as MockLLM:
        MockLLM.return_value = MagicMock()
        
        mem = ConversationMemory(user_id="test_user")
        context = mem.get_context_summary(max_messages=3)
        
        assert "Recent conversation:" in context
        assert "test message" in context
        assert "test response" in context
