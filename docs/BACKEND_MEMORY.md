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
4. Periodically or on threshold, we compact older messages into a summary and delete the raw docs.

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
- `pytest` (for tests)

## Testing
- `backend/tests/test_memory.py`
  - Mocks Firestore + LLM to validate summary compaction
  - Ensures VectorMemory gracefully handles missing Redis configuration
- `backend/tests/conftest.py`
  - Pytest fixture to ensure the backend `app` module is importable

Run tests:
```bash
cd backend
pytest ./tests/test_memory.py -v
```

Current status: ✅ 2/2 tests passing (no deprecation warnings)

## Future Work
- Add scheduled compaction based on message counts per user
- Store summary token counts and last compacted watermark
- Add metadata filters for project/context in vector store
- Evaluate Redis schema tuning and index options for scale
