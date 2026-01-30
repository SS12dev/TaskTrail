"""
Supervisor Agent for LangGraph Multi-Agent System.

This agent analyzes user requests and routes them to the most appropriate
specialized agent (Planner, Executor, Query, or Conversation).
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.agent_state import AgentState
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)

SUPERVISOR_SYSTEM_PROMPT = """You are a routing supervisor for TaskTrail, an AI-powered task management system.

Your job is to analyze the user's message and route it to the most appropriate specialized agent:

**Agents:**
- **planner**: For breaking down complex tasks, brainstorming, project planning, creating subtasks
  - Examples: "Break down 'Launch website' into steps", "Help me plan my week", "What tasks are needed for..."

- **executor**: For creating, updating, or deleting tasks/projects
  - Examples: "Create a task", "Mark task as done", "Delete my old tasks", "Update priority", "Create a project"
  - **Important**: Route to executor when users want to create multiple related tasks - suggest creating a project first!

- **query**: For searching, filtering, and getting insights about tasks
  - Examples: "Show my high priority tasks", "What's due today?", "Find tasks about...", "How many tasks..."

- **conversation**: For general help, questions about capabilities, greetings, unclear requests
  - Examples: "Hello", "What can you do?", "Help me understand", general conversation

**Project Organization Philosophy:**
- Projects are MAIN FOLDERS that contain related tasks
- Always consider if related tasks should be grouped in a project
- Suggest project creation for any multi-task workflow

**Instructions:**
- Analyze the user's intent carefully
- Consider conversation history for context
- Choose ONE agent that best fits the request
- Provide brief reasoning for your choice

**User Context:**
{user_context}
Use the user's current time/timezone when interpreting time-related requests (e.g., "today", "tomorrow").

Respond with JSON:
{{
    "agent": "planner|executor|query|conversation",
    "reasoning": "Why this agent is most appropriate",
    "confidence": "high|medium|low"
}}
"""


class SupervisorAgent:
    """Routes requests to specialized agents."""

    def __init__(self):
        """Initialize the supervisor agent with GPT-4."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,  # Lower for more consistent routing
            api_key=settings.openai_api_key
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SUPERVISOR_SYSTEM_PROMPT),
            ("human", "User message: {message}\n\nRecent context: {context}\n\nRoute this request.")
        ])

        self.chain = self.prompt | self.llm

    def _get_user_context(self, state: AgentState) -> str:
        """Build user context string for the supervisor prompt."""
        context_str = ""
        if state.get("detailed_user_context"):
            ctx = state["detailed_user_context"]
            try:
                ts_fmt = ctx["current_timestamp"].strftime('%B %d, %Y at %I:%M %p')
            except Exception:
                ts_fmt = str(ctx.get("current_timestamp"))
            context_str = (
                f"Current Time: {ts_fmt}\n"
                f"Timezone: {ctx.get('timezone', 'UTC')} (Day: {ctx.get('day_of_week', 'Unknown')}, "
                f"Time: {ctx.get('time_of_day', 'Unknown')})"
            )
        else:
            context_str = "UTC, no specific context"

        return context_str

    async def route(self, state: AgentState) -> dict:
        """
        Determine which agent should handle the request.

        Args:
            state: Current agent state

        Returns:
            Updated state with routing decision
        """
        try:
            # Get user's latest message
            last_message = state["messages"][-1]
            logger.debug(f"Supervisor - Last message type: {type(last_message)}")

            # Handle both dict and LangChain message objects
            if hasattr(last_message, 'content'):
                user_message = last_message.content
            elif isinstance(last_message, dict):
                user_message = last_message["content"]
            else:
                logger.warning(f"Unexpected message type in supervisor: {type(last_message)}")
                user_message = str(last_message)

            logger.info(f"Supervisor routing message: {user_message[:100]}...")

            # Build context from recent messages
            context = self._build_context(state["messages"][-5:])

            # Build user context for prompt
            user_context = self._get_user_context(state)

            # Call LLM to route
            response = await self.chain.ainvoke({
                "message": user_message,
                "context": context,
                "user_context": user_context
            })

            # Parse response
            try:
                routing = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to conversation agent if parsing fails
                logger.warning("Failed to parse supervisor routing, defaulting to conversation")
                routing = {
                    "agent": "conversation",
                    "reasoning": "Failed to parse routing",
                    "confidence": "low"
                }

            logger.info(f"Supervisor routed to {routing['agent']}: {routing['reasoning']}")

            return {
                **state,
                "active_agent": routing["agent"],
                "current_intent": routing["agent"],
                "agents_called": state.get("agents_called", []) + [routing["agent"]]
            }

        except Exception as e:
            logger.error(f"Error in supervisor routing: {str(e)}")
            # Default to conversation agent on error
            return {
                **state,
                "active_agent": "conversation",
                "current_intent": "conversation",
                "agents_called": state.get("agents_called", []) + ["conversation"],
                "error_message": f"Routing error: {str(e)}"
            }

    def _build_context(self, messages: list) -> str:
        """
        Build context summary from recent messages.

        Args:
            messages: List of recent messages

        Returns:
            Context string
        """
        if len(messages) <= 1:
            return "No previous context"

        context = ""
        for msg in messages[:-1]:  # Exclude current message
            # Handle both dict and LangChain message objects
            if hasattr(msg, 'type'):
                # LangChain message object
                role = msg.type  # 'human', 'ai', 'system'
                content = str(msg.content)[:100]  # Truncate
            elif isinstance(msg, dict):
                # Dictionary format
                role = msg.get("role", "unknown")
                content = str(msg.get("content", ""))[:100]
            else:
                logger.warning(f"Unexpected message type in context: {type(msg)}")
                continue

            context += f"{role}: {content}...\n"

        return context
