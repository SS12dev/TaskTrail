"""
Multi-Agent System with LangGraph Orchestration.

This module implements the complete multi-agent system using LangGraph's
StateGraph to coordinate between specialized agents.
"""

from langgraph.graph import StateGraph, END
from app.models.agent_state import AgentState
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.query_agent import QueryAgent
from app.agents.conversation_agent import ConversationAgent
from app.services.conversation_memory import ConversationMemory
from app.services.user_preferences import UserPreferences
from app.services.task_service import TaskService
from app.services.project_service import ProjectService
from app.services.token_tracker import get_token_tracker
from app.config import settings
from typing import Literal
from datetime import datetime
from langchain_core.callbacks import BaseCallbackHandler
import logging

logger = logging.getLogger(__name__)


class TokenTrackingCallback(BaseCallbackHandler):
    """Callback handler to track OpenAI token usage."""
    
    def __init__(self, user_id: str):
        """Initialize callback with user ID for tracking."""
        super().__init__()
        self.user_id = user_id
        self.total_tokens = 0
        self.model_name = settings.openai_model
        
    def on_llm_end(self, response, **kwargs):
        """Track token usage when LLM call completes."""
        try:
            # Extract token usage from response
            if hasattr(response, 'llm_output') and response.llm_output:
                token_usage = response.llm_output.get('token_usage', {})
                total_tokens = token_usage.get('total_tokens', 0)
                
                if total_tokens > 0:
                    self.total_tokens += total_tokens
                    
                    # Record usage in token tracker
                    tracker = get_token_tracker()
                    tracker.record_usage(
                        user_id=self.user_id,
                        tokens=total_tokens,
                        model=self.model_name
                    )
                    
                    logger.info(f"Tracked {total_tokens} tokens for user {self.user_id} (model: {self.model_name})")
                    
        except Exception as e:
            logger.error(f"Error tracking token usage: {str(e)}", exc_info=True)
            # Don't fail the request if tracking fails


class MultiAgentSystem:
    """LangGraph-based multi-agent system for TaskTrail."""

    def __init__(self, user_id: str):
        """
        Initialize the multi-agent system for a user.

        Args:
            user_id: The user's Firebase UID
        """
        self.user_id = user_id

        # Initialize services
        self.conversation_memory = ConversationMemory(user_id)
        self.user_prefs = UserPreferences(user_id)
        self.task_service = TaskService()
        self.project_service = ProjectService()
        
        # Initialize token tracking callback
        self.token_callback = TokenTrackingCallback(user_id)

        # Initialize agents
        self.supervisor = SupervisorAgent()
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(user_id)
        self.query = QueryAgent(user_id)
        self.conversation = ConversationAgent()

        # Build and compile graph
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()

        logger.info(f"Multi-agent system initialized for user {user_id}")

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph.

        Returns:
            Compiled StateGraph
        """
        # Create graph with our state schema
        graph = StateGraph(AgentState)

        # Add nodes for each agent
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("planner", self._planner_node)
        graph.add_node("executor", self._executor_node)
        graph.add_node("query", self._query_node)
        graph.add_node("conversation", self._conversation_node)

        # Set entry point
        graph.set_entry_point("supervisor")

        # Add conditional routing from supervisor
        graph.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "planner": "planner",
                "executor": "executor",
                "query": "query",
                "conversation": "conversation"
            }
        )

        # All agents end the conversation
        graph.add_edge("planner", END)
        graph.add_edge("executor", END)
        graph.add_edge("query", END)
        graph.add_edge("conversation", END)

        return graph

    async def _supervisor_node(self, state: AgentState) -> dict:
        """Supervisor routing node."""
        return await self.supervisor.route(state)

    async def _planner_node(self, state: AgentState) -> dict:
        """Planner agent node."""
        return await self.planner.process(state)

    async def _executor_node(self, state: AgentState) -> dict:
        """Executor agent node."""
        return await self.executor.process(state)

    async def _query_node(self, state: AgentState) -> dict:
        """Query agent node."""
        return await self.query.process(state)

    async def _conversation_node(self, state: AgentState) -> dict:
        """Conversation agent node."""
        return await self.conversation.process(state)

    def _route_from_supervisor(
        self,
        state: AgentState
    ) -> Literal["planner", "executor", "query", "conversation"]:
        """
        Route based on supervisor's decision.

        Args:
            state: Current agent state

        Returns:
            Agent name to route to
        """
        agent = state.get("active_agent", "conversation")

        # Validate and return
        valid_agents = ["planner", "executor", "query", "conversation"]
        return agent if agent in valid_agents else "conversation"

    async def process_message(self, user_message: str) -> str:
        """
        Main entry point for processing user messages.

        Args:
            user_message: User's input text

        Returns:
            Assistant's response text
        """
        try:
            # Build user context
            user_context = await self._build_user_context()

            # Load recent conversation history for context
            recent_history = self.conversation_memory.get_recent_history(limit=10)
            logger.info(f"Loaded {len(recent_history)} messages from conversation history")

            # Build messages list from history + new message
            messages = []
            for hist_msg in recent_history:
                # Add user message
                if hist_msg.get("user_message"):
                    messages.append({
                        "role": "user",
                        "content": hist_msg["user_message"],
                        "timestamp": hist_msg.get("timestamp", datetime.now()).isoformat() if hist_msg.get("timestamp") else datetime.now().isoformat()
                    })
                # Add assistant response
                if hist_msg.get("agent_response"):
                    messages.append({
                        "role": "assistant",
                        "content": hist_msg["agent_response"],
                        "timestamp": hist_msg.get("timestamp", datetime.now()).isoformat() if hist_msg.get("timestamp") else datetime.now().isoformat()
                    })

            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })

            logger.debug(f"Total messages in context: {len(messages)}")

            # Initialize state
            initial_state = AgentState(
                messages=messages,
                user_context=user_context,
                task_context={
                    "task_id": None,
                    "title": None,
                    "description": None,
                    "priority": None,
                    "due_date": None,
                    "tags": [],
                    "project_id": None,
                    "subtasks": []
                },
                current_intent=None,
                active_agent=None,
                agents_called=[],
                last_action=None,
                last_result=None,
                error_message=None,
                iteration_count=0
            )

            # Run through graph
            logger.info(f"Processing message through LangGraph for user {self.user_id}")
            final_state = await self.compiled_graph.ainvoke(
                initial_state,
                config={"callbacks": [self.token_callback]}
            )
            logger.info(f"LangGraph processing completed. Agents called: {final_state.get('agents_called', [])}")
            logger.info(f"Total tokens used: {self.token_callback.total_tokens}")

            # Extract response from LangChain message object
            last_message = final_state["messages"][-1]
            logger.debug(f"Last message type: {type(last_message)}")

            # Handle both dict and LangChain message objects
            if hasattr(last_message, 'content'):
                # LangChain message object (AIMessage, HumanMessage, etc.)
                response = last_message.content
            elif isinstance(last_message, dict):
                # Dictionary format
                response = last_message["content"]
            else:
                logger.error(f"Unexpected message type: {type(last_message)}")
                response = str(last_message)

            logger.info(f"Extracted response: {response[:100]}...")

            # Save conversation to Firestore
            self.conversation_memory.save_message(
                user_message,
                response,
                metadata={
                    "agents_called": final_state.get("agents_called", []),
                    "intent": final_state.get("current_intent"),
                    "action": final_state.get("last_action")
                }
            )

            logger.info(f"Message processed successfully for user {self.user_id}")
            return response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            error_msg = f"I encountered an error: {str(e)}. Please try rephrasing your request."

            # Still save to conversation history
            self.conversation_memory.save_message(
                user_message,
                error_msg,
                metadata={"error": str(e)}
            )

            return error_msg

    async def _build_user_context(self) -> dict:
        """
        Build context about the user.

        Returns:
            User context dictionary
        """
        try:
            # Get user preferences
            prefs = self.user_prefs.get_preferences()

            # Get user's projects
            projects = await self.project_service.list_projects(self.user_id)

            # Get task count
            tasks = await self.task_service.list_tasks(self.user_id)

            return {
                "user_id": self.user_id,
                "email": None,  # Could be populated from auth
                "current_projects": [p.id for p in projects.projects],
                "task_count": len(tasks.tasks),
                "preferences": prefs
            }

        except Exception as e:
            logger.error(f"Error building user context: {str(e)}")
            # Return minimal context on error
            return {
                "user_id": self.user_id,
                "email": None,
                "current_projects": [],
                "task_count": 0,
                "preferences": {}
            }
