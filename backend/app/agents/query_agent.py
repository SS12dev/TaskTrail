"""
Query Agent for LangGraph Multi-Agent System.

This agent handles task search, filtering, and analytics queries.
It uses tools to query tasks from Firestore and format results nicely.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from app.models.agent_state import AgentState, ConversationMessage
from app.agents.prompt_builder import PromptBuilder
from app.agents.tools.task_tools import TaskTools
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

QUERY_SYSTEM_PROMPT = """You are a task query and analytics assistant for TaskTrail.

Your role is to help users find and understand their tasks:
- Search tasks by status, priority, project, tags
- Provide insights about task patterns
- Answer questions about task organization
- Suggest task priorities based on queries

**Available Tools:**
- list_tasks: Query tasks with filters
- get_today_tasks: Get smart inbox (overdue + due today + high priority)

**Guidelines:**
1. Interpret user's query intent (e.g., "important tasks" = high/urgent priority)
2. Use appropriate filters to narrow results
3. Format results clearly with counts and summaries
4. Provide helpful insights when relevant
5. If no tasks match, suggest alternatives

Always present results in an easy-to-read format with task details.
"""


class QueryAgent:
    """Queries and analyzes tasks."""

    def __init__(self, user_id: str):
        """
        Initialize the query agent with tools.

        Args:
            user_id: The user's Firebase UID
        """
        self.user_id = user_id

        # Initialize tools (only query tools, not mutation tools)
        task_tools = TaskTools(user_id)
        all_tools = task_tools.get_all_tools()

        # Filter to only include query tools
        self.tools = [tool for tool in all_tools if tool.name in ["list_tasks", "get_today_tasks"]]

        # Create LLM with tool binding
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.5,
            api_key=settings.openai_api_key
        )

        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def process(self, state: AgentState) -> dict:
        """
        Process query request.

        Args:
            state: Current agent state

        Returns:
            Updated state with query results
        """
        try:
            # Get user's latest message
            last_message = state["messages"][-1]
            logger.debug(f"Query agent - Message type: {type(last_message)}")

            # Handle both dict and LangChain message objects
            if hasattr(last_message, 'content'):
                user_message = last_message.content
            elif isinstance(last_message, dict):
                user_message = last_message["content"]
            else:
                logger.warning(f"Unexpected message type: {type(last_message)}")
                user_message = str(last_message)

            logger.info(f"Query agent processing: {user_message[:100]}...")

            # Build context-aware query prompt
            system_prompt = PromptBuilder.build_query_prompt(QUERY_SYSTEM_PROMPT, state)
            system_prompt = PromptBuilder.attach_memory_context(system_prompt, state.get("memory_context"))
            
            # Add task/project context to improve query results
            query_context = ""
            if state.get("project_id"):
                query_context += f"\nNote: User is currently in project context (project_id={state['project_id']}).\n"
                query_context += "Consider filtering results to this project if relevant."
            
            if state.get("task_id"):
                query_context += f"\nNote: User is currently viewing task (task_id={state['task_id']}).\n"
                query_context += "Consider providing related task information when relevant."
            
            if query_context:
                system_prompt += f"\n\n**Current Context:**{query_context}"

            # Create messages for LLM
            messages = [
                ("system", system_prompt),
                ("human", user_message)
            ]

            # Call LLM with tools
            logger.debug("Calling LLM with query tools")
            response = await self.llm_with_tools.ainvoke(messages)
            logger.info(f"Query LLM response received with {len(response.tool_calls) if hasattr(response, 'tool_calls') else 0} tool calls")

            # Check if LLM wants to call tools
            if response.tool_calls:
                # Execute tool calls
                tool_results = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    # Find and execute the tool
                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if tool:
                        result = await tool.ainvoke(tool_args)
                        tool_results.append(result)

                # Generate final response based on tool results
                final_messages = messages + [
                    ("assistant", str(response.content) if response.content else "Querying tasks..."),
                    ("human", f"Tool results: {tool_results}. Please provide a summary response to the user.")
                ]
                final_response = await self.llm.ainvoke(final_messages)
                response_content = final_response.content
            else:
                response_content = response.content

            # Create response message
            assistant_message = ConversationMessage(
                role="assistant",
                content=response_content,
                timestamp=datetime.now().isoformat()
            )

            logger.info(f"Query agent completed: {response_content[:100] if response_content else 'empty'}")

            return {
                **state,
                "messages": state["messages"] + [assistant_message],
                "last_action": "query",
                "last_result": {"status": "success"}
            }

        except Exception as e:
            logger.error(f"Error in query agent: {str(e)}")
            error_message = ConversationMessage(
                role="assistant",
                content=f"I encountered an error while querying tasks: {str(e)}. Please try again.",
                timestamp=datetime.now().isoformat()
            )

            return {
                **state,
                "messages": state["messages"] + [error_message],
                "last_action": "query",
                "last_result": {"status": "error"},
                "error_message": str(e)
            }
