# Backend Memory Architecture

This document tracks the implementation of memory and context features in TaskTrail.

## Overview
- Short-term storage: Firestore `conversations/{userId}/messages`
- Compacted summaries: Firestore `conversations/{userId}/summaries`
- Semantic recall: Redis vector store (OpenAI embeddings via LangChain)

## Components
- ConversationMemory (Firestore)
  - `save_message(user_message, agent_response, metadata)`
  - `get_recent_history(limit)`
  - `get_context_summary(max_messages)`
  - `summarize_and_compact(retain_last)`
- VectorMemory (Redis + OpenAI Embeddings)
  - `add_turn(user_id, text, metadata)`
  - `search(user_id, query, k)`

## Data Flow
1. After each agent turn, we save the pair (user, assistant) to Firestore.
2. The same turn is indexed into Redis vector store with metadata `{ user_id, ... }`.
3. On each new request, we:
   - Build a short context summary of the last few turns
   - Search Redis for top-k similar past turns by the user's latest message
   - Attach both pieces as `memory_context` to prompts
4. **Auto-compaction**: After saving each conversation:
   - Check message count (threshold: 50 messages)
   - If exceeded, compact older messages into summary (retains last 20)
   - Summary stored in `summaries` subcollection, old messages deleted
   - Runs automatically in background, graceful error handling

## Configuration
Environment (.env):
- `REDIS_URL=redis://localhost:6379/0`
- `REDIS_INDEX_NAME=tasktrail_memory`
- `OPENAI_API_KEY=...`

App settings in `app/config.py`:
- `redis_url`, `redis_index_name`, `redis_namespace`

## Dependencies
Added to `backend/requirements.txt`:
- `redis`
- `langchain-community`
- `langchain-redis`
- `pytest` (for tests)

## Testing

### Unit Tests (`backend/tests/test_memory.py`)
- ✅ `test_conversation_summary_generation` - Validates LLM-based summarization
- ✅ `test_vector_memory_add_and_search` - Ensures Redis vector operations work
- ✅ `test_auto_compaction_threshold` - Verifies auto-compaction triggers correctly
- ✅ `test_memory_context_integration` - Tests context building pipeline

### E2E Tests (`backend/tests/test_e2e_memory.py`)
- ⏭️ `test_e2e_memory_flow` - Full integration test (skipped in CI, requires Firebase)
- ✅ `test_memory_graceful_degradation` - Validates fallback behavior

### Setup
- `backend/tests/conftest.py` - Pytest fixture for module imports

Run tests:
```bash
cd backend
pytest ./tests/ -v
```

**Current status**: ✅ 5/6 tests passing (1 skipped E2E, 0 failures)

## Implementation Status

✅ **Completed**:
- ConversationMemory with Firestore persistence
- VectorMemory with Redis + OpenAI embeddings
- Memory context injection into agent prompts
- Auto-compaction at 50-message threshold
- Comprehensive test coverage (5/6 passing)
- Graceful degradation when Redis unavailable

## Future Enhancements
- [ ] Configurable compaction threshold per user
- [ ] Scheduled background compaction (cron job)
- [ ] Project/task-specific memory namespaces
- [ ] Memory analytics dashboard
- [ ] Export conversation history API
- [ ] Semantic search UI for users to query their history
- Store summary token counts and last compacted watermark
- Add metadata filters for project/context in vector store
- Evaluate Redis schema tuning and index options for scale
