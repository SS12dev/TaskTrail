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
                    self.agent_system.conversation_memory.save_message(
                        user_msg["content"],
                        assistant_msg["content"],
                        metadata={
                            "agents_called": final_state.get("agents_called", []),
                            "intent": final_state.get("current_intent"),
                            "action": final_state.get("last_action"),
                        }
                    )

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
