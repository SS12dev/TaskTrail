"""
Executor Agent for LangGraph Multi-Agent System.

This agent performs actual task operations (create, update, delete) by calling
the task and project tools integrated with the TaskService.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from app.models.agent_state import AgentState, ConversationMessage
from app.agents.prompt_builder import PromptBuilder
from app.agents.tools.task_tools import TaskTools
from app.agents.tools.project_tools import ProjectTools
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

EXECUTOR_SYSTEM_PROMPT = """You are a task execution assistant for TaskTrail.

Your role is to TAKE ACTION and perform task operations based on user requests:
- Create new tasks with appropriate details
- Update existing tasks (status, priority, dates)
- Delete tasks
- Create projects for organization

**PROJECT-FIRST PHILOSOPHY:**
- Projects are MAIN FOLDERS that contain related tasks
- When creating multiple related tasks, ALWAYS suggest/create a project first
- Projects help users track progress and organize work hierarchically
- Example: "Website Redesign" project → contains tasks like "Design mockups", "Write content", etc.
- Use project_id when creating tasks that belong to a project

**IMPORTANT - Date Format Instructions:**
When you call create_task or update_task, ALWAYS provide dates in one of these formats:
1. ISO format: YYYY-MM-DD (e.g., "2026-01-27" for tomorrow)
2. Natural language: "tomorrow", "next week", "next friday" - the system will convert these

**Important Guidelines:**
1. BE PROACTIVE - Don't ask for details, make reasonable assumptions
2. When user asks for "sample tasks" or "test tasks", CREATE a project first, then 3-5 tasks within it
3. Use appropriate defaults for missing information (medium priority, due date in 3-7 days)
4. Interpret relative dates ("tomorrow", "next week", "friday") and convert to YYYY-MM-DD
5. TODAY'S DATE IS: """ + datetime.now().strftime("%Y-%m-%d") + """
6. ALWAYS call tools to perform actual operations - never just explain what you would do
7. Provide clear confirmation of what was done
8. When creating tasks for a project, ALWAYS include the project_id parameter

**Available Tools:**
- create_task: Create a new task
- update_task: Update an existing task
- delete_task: Delete a task
- create_project: Create a new project
- list_tasks: Query tasks (use when you need to find a task ID)

**CRITICAL - Project Task Association:**
When creating tasks for a project, ALWAYS include the project_id parameter:
- Example: create_task(title="Task Name", description="...", project_id="project123")
- Look for project mentions in the conversation to find the project ID
- If user is discussing a specific project, associate all new tasks with it

**Examples:**
- User: "create a task tomorrow at 6pm" → Call create_task with due_date="2026-01-27" (tomorrow)
- User: "create all these tasks for Fintech Website" → Create project first if needed, then create_task with project_id
- User: "create sample tasks" → CREATE a project first, then 3-5 tasks within it using project_id
- User: "create a task for next friday" → Call create_task with due_date="2026-01-31" (next friday)

Always call tools and confirm the action taken with a friendly message showing what you created.
"""


class ExecutorAgent:
    """Executes task and project operations."""

    def __init__(self, user_id: str):
        """
        Initialize the executor agent with tools.

        Args:
            user_id: The user's Firebase UID
        """
        self.user_id = user_id

        # Initialize tools
        task_tools = TaskTools(user_id)
        project_tools = ProjectTools(user_id)

        self.tools = task_tools.get_all_tools() + project_tools.get_all_tools()

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
        Execute task operations.

        Args:
            state: Current agent state

        Returns:
            Updated state with execution results
        """
        try:
            # Get user's latest message
            last_message = state["messages"][-1]
            logger.debug(f"Executor agent - Message type: {type(last_message)}")

            # Handle both dict and LangChain message objects
            if hasattr(last_message, 'content'):
                user_message = last_message.content
            elif isinstance(last_message, dict):
                user_message = last_message["content"]
            else:
                logger.warning(f"Unexpected message type: {type(last_message)}")
                user_message = str(last_message)

            logger.info(f"Executor agent processing: {user_message[:100]}...")

            # Extract project context from conversation history
            project_id = state.get("project_id")
            if not project_id and state.get("messages"):
                # Try to find project mentions in recent conversation
                from app.services.project_service import ProjectService
                project_service = ProjectService()
                projects = await project_service.list_projects(self.user_id)
                
                # Search recent messages for project mentions
                recent_text = " ".join([
                    msg.get("content", "") if isinstance(msg, dict) else getattr(msg, 'content', '')
                    for msg in state["messages"][-5:]  # Last 5 messages
                ])
                
                # Find which project is mentioned most recently
                for project in projects.projects:
                    if project.name.lower() in recent_text.lower():
                        project_id = project.id
                        logger.info(f"Extracted project context from conversation: {project.name} ({project_id})")
                        break

            # Add context about previous planning if available
            context = ""
            if state.get("task_context", {}).get("subtasks"):
                context = f"\nNote: User previously planned subtasks: {state['task_context']['subtasks']}"
                context += "\nConsider creating these subtasks if the user requests it."
            
            # Add task-aware context if task_id is in state
            if state.get("task_id"):
                context += f"\nCurrent task context: task_id={state['task_id']}"
                try:
                    # Try to fetch task details for context
                    task_tools = TaskTools(self.user_id)
                    # Add reference to current task ID
                    context += "\nWhen modifying this task, ensure you use the correct task ID provided above."
                except Exception as e:
                    logger.debug(f"Could not load task details: {e}")
            
            # Add project-aware context if project_id is in state or extracted
            if project_id:
                context += f"\n\n🎯 **PROJECT CONTEXT**: You are creating tasks for a specific project."
                context += f"\nAlways pass project_id='{project_id}' when creating tasks with create_task() tool."
                context += "\nEach task created must include this project_id parameter."

            # Build context-aware system prompt
            system_prompt = PromptBuilder.build_executor_prompt(EXECUTOR_SYSTEM_PROMPT, state)
            system_prompt = PromptBuilder.attach_memory_context(system_prompt, state.get("memory_context"))
            
            # Add task/project context to system prompt
            if context:
                system_prompt += f"\n\n**Current Context:**{context}"

            # Create messages for LLM
            messages = [
                ("system", system_prompt),
                ("human", user_message + context)
            ]

            # Call LLM with tools
            logger.debug("Calling LLM with tools for task execution")
            response = await self.llm_with_tools.ainvoke(messages)
            logger.info(f"Executor LLM response received with {len(response.tool_calls) if hasattr(response, 'tool_calls') else 0} tool calls")

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
                    ("assistant", str(response.content) if response.content else "Executing operations..."),
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

            logger.info(f"Executor agent completed: {response_content[:100] if response_content else 'empty'}")

            return {
                **state,
                "messages": state["messages"] + [assistant_message],
                "last_action": "execution",
                "last_result": {"status": "success"}
            }

        except Exception as e:
            logger.error(f"Error in executor agent: {str(e)}", exc_info=True)
            error_message = ConversationMessage(
                role="assistant",
                content=f"I encountered an error while executing the task: {str(e)}. Please try again.",
                timestamp=datetime.now().isoformat()
            )

            return {
                **state,
                "messages": state["messages"] + [error_message],
                "last_action": "execution",
                "last_result": {"status": "error"},
                "error_message": str(e)
            }
