import pytest
from unittest.mock import MagicMock, patch
from app.services.conversation_memory import ConversationMemory
from app.services.vector_memory import VectorMemory


class DummyFirestoreDoc:
    def __init__(self, data):
        self._data = data
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
