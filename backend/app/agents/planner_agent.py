"""
Planner Agent for LangGraph Multi-Agent System.

This agent helps users break down complex projects into manageable subtasks,
provides planning assistance, and offers brainstorming support.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.agent_state import AgentState, ConversationMessage
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are a planning and brainstorming assistant for TaskTrail.

Your specialties:
- Breaking down complex projects into manageable subtasks
- Suggesting task organization and prioritization
- Brainstorming ideas and approaches
- Creating structured plans with clear steps

**Be Proactive:**
- When asked for "task variations" or "sample tasks", provide 5-7 diverse, concrete task ideas immediately
- Don't ask for clarification unless the request is truly ambiguous
- Provide actionable, specific task suggestions with priorities and estimated effort

When breaking down a task or suggesting variations:
1. Identify the main goal or context
2. List 5-7 concrete, actionable tasks/subtasks
3. Include diverse types (testing, documentation, implementation, review, etc.)
4. Suggest priority levels (high, medium, low)
5. Recommend a logical order
6. Consider dependencies and categorization

**Format your response clearly:**
- Use numbered lists
- Include task title, description, priority
- Group related tasks if applicable

Always be specific and actionable. Respond immediately with concrete suggestions.
"""


class PlannerAgent:
    """Breaks down projects and helps with planning."""

    def __init__(self):
        """Initialize the planner agent with GPT-4."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            api_key=settings.openai_api_key
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PLANNER_SYSTEM_PROMPT),
            ("human", "{message}")
        ])

        self.chain = self.prompt | self.llm

    async def process(self, state: AgentState) -> dict:
        """
        Process planning/brainstorming request.

        Args:
            state: Current agent state

        Returns:
            Updated state with planning response
        """
        try:
            # Get user's latest message
            last_message = state["messages"][-1]
            logger.debug(f"Planner agent - Message type: {type(last_message)}")

            # Handle both dict and LangChain message objects
            if hasattr(last_message, 'content'):
                user_message = last_message.content
            elif isinstance(last_message, dict):
                user_message = last_message["content"]
            else:
                logger.warning(f"Unexpected message type: {type(last_message)}")
                user_message = str(last_message)

            logger.info(f"Planner agent processing: {user_message[:100]}...")

            # Call LLM to generate plan
            response = await self.chain.ainvoke({"message": user_message})
            logger.info(f"Planner response received: {response.content[:100]}...")

            # Extract subtasks if this is a breakdown request
            subtasks = self._extract_subtasks(response.content, user_message)

            # Create response message
            assistant_message = ConversationMessage(
                role="assistant",
                content=response.content,
                timestamp=datetime.now().isoformat()
            )

            logger.info(f"Planner generated {len(subtasks)} subtasks")

            return {
                **state,
                "messages": state["messages"] + [assistant_message],
                "task_context": {
                    **state.get("task_context", {}),
                    "subtasks": subtasks
                },
                "last_action": "planning",
                "last_result": {"status": "success", "subtasks_generated": len(subtasks)}
            }

        except Exception as e:
            logger.error(f"Error in planner agent: {str(e)}")
            error_message = ConversationMessage(
                role="assistant",
                content=f"I encountered an error while planning: {str(e)}. Could you rephrase your request?",
                timestamp=datetime.now().isoformat()
            )

            return {
                **state,
                "messages": state["messages"] + [error_message],
                "last_action": "planning",
                "last_result": {"status": "error"},
                "error_message": str(e)
            }

    def _extract_subtasks(self, response: str, original_message: str) -> list:
        """
        Extract structured subtasks from LLM response.

        Args:
            response: LLM response text
            original_message: Original user message

        Returns:
            List of subtask dictionaries
        """
        subtasks = []
        lines = response.split("\n")

        for line in lines:
            # Match patterns like "1. Task name" or "- Task name"
            if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("-")):
                # Clean up the line
                task_title = line.strip().lstrip("0123456789.-) ").strip()
                if task_title and len(task_title) > 5:  # Reasonable task name
                    subtasks.append({
                        "title": task_title,
                        "priority": "medium",
                        "status": "todo"
                    })

        return subtasks[:10]  # Max 10 subtasks
