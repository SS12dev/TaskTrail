"""
LangGraph Multi-Agent Service for TaskTrail.

This service provides AI-powered task management using a sophisticated
multi-agent system with OpenAI GPT-4 and LangGraph orchestration.
"""

from app.agents.multi_agent_system import MultiAgentSystem
from app.models.agent_state import AgentState
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
from app.services.user_preferences import UserPreferences

# Cache agent systems per user for performance
_agent_systems: Dict[str, MultiAgentSystem] = {}


class AgentService:
    """AI Agent service powered by LangGraph multi-agent system."""

    def __init__(self, user_id: str):
        """
        Initialize agent service for a user.

        Args:
            user_id: The user's Firebase UID
        """
        self.user_id = user_id

        # Get or create agent system for this user
        if user_id not in _agent_systems:
            logger.info(f"Initializing multi-agent system for user {user_id}")
            _agent_systems[user_id] = MultiAgentSystem(user_id)

        self.agent_system = _agent_systems[user_id]

    async def process_text_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Process a text message through the multi-agent system (legacy API).

        Args:
            user_id: The user's ID (for validation)
            message: The user's message

        Returns:
            Dict containing the response and metadata
        """
        # Validate user_id matches
        if user_id != self.user_id:
            return {
                "type": "error",
                "message": "User ID mismatch. Please refresh and try again."
            }

        try:
            # Process through LangGraph multi-agent system
            response = await self.agent_system.process_message(message)

            return {
                "type": "response",
                "message": response,
                "task": None,  # Can be populated by executor agent
                "tasks": None  # Can be populated by query agent
            }

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {str(e)}")
            return {
                "type": "error",
                "message": "I encountered an error processing your request. Please try again or rephrase your message."
            }

    async def process_message(self, state: AgentState) -> AgentState:
        """
        Process an AgentState through the multi-agent system (A2A integration).

        This method is designed for A2A integration where the state
        is already formatted by the A2A adapter.

        Args:
            state: AgentState to process

        Returns:
            Final AgentState after processing
        """
        try:
            logger.info(f"AgentService processing A2A AgentState for user {self.user_id}")
            logger.debug(f"Input state - Messages: {len(state.get('messages', []))}, "
                        f"User context: {state.get('user_context', {}).get('user_id')}")

            # Build user context with timezone information
            user_prefs = UserPreferences(self.user_id)
            user_context_obj = await user_prefs.get_user_context()

            # Add detailed user context to state
            state["detailed_user_context"] = {
                "current_timestamp": user_context_obj.current_timestamp,
                "timezone": user_context_obj.timezone,
                "locale": user_context_obj.locale,
                "country": user_context_obj.country,
                "day_of_week": user_context_obj.day_of_week,
                "time_of_day": user_context_obj.time_of_day,
            }

            logger.debug(f"Built user context: {user_context_obj.timezone} - {user_context_obj.current_timestamp}")

            # Build memory context (recent summary + vector recall with filtering)
            memory_snippets = []
            try:
                from app.services.conversation_memory import ConversationMemory
                from app.services.vector_memory import VectorMemory
                from app.services.memory_filters import build_memory_context_for_task, build_memory_context_for_project
                
                # Extract project/task context if present in state
                project_id = state.get("project_id")
                task_id = state.get("task_id")
                agent_type = state.get("current_agent")
                
                conv_mem = ConversationMemory(self.user_id)
                
                # Build context using appropriate filter based on scope
                if task_id and project_id:
                    # Task-specific memory context
                    recent_summary = conv_mem.get_context_summary(max_messages=5)
                    last_msg = state.get("messages", [])[-1] if state.get("messages") else None
                    query_text = last_msg.content if hasattr(last_msg, 'content') else (last_msg.get('content') if isinstance(last_msg, dict) else None)
                    
                    vec = VectorMemory()
                    vector_results = vec.filtered_search(
                        self.user_id, 
                        query_text or "", 
                        project_id=project_id,
                        task_id=task_id,
                        agent_type=agent_type,
                        k=3
                    )
                    
                    # Use task-aware context builder
                    task_context = build_memory_context_for_task(
                        task_id=task_id,
                        recent_history=recent_summary.split("\n") if recent_summary else [],
                        vector_results=vector_results
                    )
                    if task_context:
                        memory_snippets.append(task_context)
                
                elif project_id:
                    # Project-specific memory context
                    recent_summary = conv_mem.get_context_summary(max_messages=5)
                    last_msg = state.get("messages", [])[-1] if state.get("messages") else None
                    query_text = last_msg.content if hasattr(last_msg, 'content') else (last_msg.get('content') if isinstance(last_msg, dict) else None)
                    
                    vec = VectorMemory()
                    vector_results = vec.filtered_search(
                        self.user_id,
                        query_text or "",
                        project_id=project_id,
                        agent_type=agent_type,
                        k=3
                    )
                    
                    # Use project-aware context builder
                    project_context = build_memory_context_for_project(
                        project_id=project_id,
                        recent_history=recent_summary.split("\n") if recent_summary else [],
                        vector_results=vector_results
                    )
                    if project_context:
                        memory_snippets.append(project_context)
                
                else:
                    # General memory context (no project/task scope)
                    recent_summary = conv_mem.get_context_summary(max_messages=5)
                    if recent_summary:
                        memory_snippets.append(recent_summary)
                    
                    # Vector recall from last user message if available
                    last_msg = state.get("messages", [])[-1] if state.get("messages") else None
                    query_text = last_msg.content if hasattr(last_msg, 'content') else (last_msg.get('content') if isinstance(last_msg, dict) else None)
                    if query_text:
                        vec = VectorMemory()
                        results = vec.search(self.user_id, query_text, k=3)
                        if results:
                            memory_snippets.append("Top relevant history:\n" + "\n".join([f"- {r['text'][:160]}" for r in results]))
                
                # Attach combined memory context
                if memory_snippets:
                    state["memory_context"] = "\n\n".join(memory_snippets)
            except Exception as e:
                logger.warning(f"Memory context build skipped: {e}")

            # Run through compiled graph
            final_state = await self.agent_system.compiled_graph.ainvoke(state)

            logger.info(f"LangGraph processing complete - Agents: {final_state.get('agents_called', [])}")
            logger.debug(f"Final state - Messages: {len(final_state.get('messages', []))}, "
                        f"Error: {final_state.get('error_message')}")

            # Save conversation to memory
            if len(final_state["messages"]) >= 2:
                # Find user and assistant messages (handle both dict and LangChain objects)
                user_msg = None
                assistant_msg = None

                for msg in final_state["messages"]:
                    if hasattr(msg, 'type'):
                        # LangChain message
                        if msg.type == 'human' and not user_msg:
                            user_msg = {"content": msg.content}
                        elif msg.type == 'ai':
                            assistant_msg = {"content": msg.content}
                    elif isinstance(msg, dict):
                        # Dict message
                        if msg.get("role") == "user" and not user_msg:
                            user_msg = msg
                        elif msg.get("role") == "assistant":
                            assistant_msg = msg

                if user_msg and assistant_msg:
                    logger.info("Saving conversation to memory")
                    
                    # Build metadata with project/task context if available
                    save_metadata = {
                        "agents_called": final_state.get("agents_called", []),
                        "intent": final_state.get("current_intent"),
                        "action": final_state.get("last_action"),
                    }
                    
                    # Add project/task context to metadata for filtering
                    if state.get("project_id"):
                        save_metadata["project_id"] = state.get("project_id")
                    if state.get("task_id"):
                        save_metadata["task_id"] = state.get("task_id")
                    if state.get("current_agent"):
                        save_metadata["agent_type"] = state.get("current_agent")
                    
                    self.agent_system.conversation_memory.save_message(
                        user_msg["content"],
                        assistant_msg["content"],
                        metadata=save_metadata
                    )
                    
                    # Auto-compaction: Check if we should compact old messages
                    await self._auto_compact_if_needed()

            logger.info(
                f"AgentState processed successfully - User: {self.user_id}, "
                f"Agents: {final_state.get('agents_called', [])}"
            )

            return final_state

        except Exception as e:
            logger.error(f"Error processing AgentState for user {self.user_id}: {str(e)}", exc_info=True)

            # Return state with error
            error_state = state.copy()
            error_state["error_message"] = str(e)
            error_state["messages"].append({
                "role": "assistant",
                "content": f"I encountered an error: {str(e)}. Please try rephrasing your request.",
                "timestamp": state["messages"][-1]["timestamp"] if state.get("messages") else datetime.now().isoformat(),
            })

            logger.info(f"Returning error state for user {self.user_id}")
            return error_state

    async def _auto_compact_if_needed(self, threshold: int = 50) -> None:
        """
        Auto-compact conversation memory if message count exceeds threshold.
        
        Args:
            threshold: Number of messages before triggering compaction (default: 50)
        """
        try:
            # Count current messages
            message_count = 0
            docs = self.agent_system.conversation_memory.conversations_ref.limit(threshold + 1).stream()
            for _ in docs:
                message_count += 1
                if message_count > threshold:
                    break
            
            if message_count > threshold:
                logger.info(f"Auto-compaction triggered for user {self.user_id} ({message_count} messages)")
                summary = self.agent_system.conversation_memory.summarize_and_compact(retain_last=20)
                if summary:
                    logger.info(f"Successfully compacted {message_count - 20} messages into summary")
                else:
                    logger.warning(f"Auto-compaction returned no summary for user {self.user_id}")
        except Exception as e:
            logger.warning(f"Auto-compaction failed for user {self.user_id}: {e}")

    @staticmethod
    def get_instance(user_id: str) -> "AgentService":
        """
        Get or create AgentService instance for a user (singleton per user).

        Args:
            user_id: User identifier

        Returns:
            AgentService instance for the user
        """
        return AgentService(user_id)

    @staticmethod
    def clear_cache(user_id: str = None):
        """
        Clear cached agent systems (for logout or memory management).

        Args:
            user_id: Specific user to clear, or None to clear all
        """
        if user_id:
            _agent_systems.pop(user_id, None)
            logger.info(f"Cleared agent system cache for user {user_id}")
        else:
            _agent_systems.clear()
            logger.info("Cleared all agent system caches")
