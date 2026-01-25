"""
Conversation Agent for LangGraph Multi-Agent System.

This agent handles general conversation, help requests, and unclear queries.
It provides a friendly interface for users to learn about TaskTrail's capabilities.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.agent_state import AgentState, ConversationMessage
from app.config import settings
from datetime import datetime
import logging
from app.agents.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

CONVERSATION_SYSTEM_PROMPT = """You are a friendly, helpful assistant for TaskTrail, an AI-powered task management system.

Your role is to:
- Greet users warmly
- Answer questions about TaskTrail's capabilities
- Provide help and guidance
- Handle unclear or ambiguous requests
- Engage in friendly conversation

**TaskTrail Capabilities:**
- Create, update, delete tasks with natural language
- Search and filter tasks by status, priority, project, tags
- Break down complex projects into subtasks
- Get smart "Today" inbox with overdue and urgent tasks
- Organize tasks into projects
- Track task priorities and due dates

**Guidelines:**
1. Be friendly, professional, and helpful
2. If a request is unclear, ask clarifying questions
3. Suggest what TaskTrail can do to help
4. Provide examples of commands users can try
5. Handle errors gracefully with suggestions

Keep responses concise and actionable.
"""


class ConversationAgent:
    """Handles general conversation and help."""

    def __init__(self):
        """Initialize the conversation agent with GPT-4."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.8,  # Slightly higher for more natural conversation
            api_key=settings.openai_api_key
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", CONVERSATION_SYSTEM_PROMPT),
            ("human", "{message}")
        ])

        self.chain = self.prompt | self.llm

    async def process(self, state: AgentState) -> dict:
        """
        Process conversational request.

        Args:
            state: Current agent state

        Returns:
            Updated state with conversation response
        """
        try:
            # Get user's latest message
            last_message = state["messages"][-1]
            logger.debug(f"Conversation agent - Message type: {type(last_message)}")

            # Handle both dict and LangChain message objects
            if hasattr(last_message, 'content'):
                user_message = last_message.content
            elif isinstance(last_message, dict):
                user_message = last_message["content"]
            else:
                logger.warning(f"Unexpected message type: {type(last_message)}")
                user_message = str(last_message)

            logger.info(f"Conversation agent processing: {user_message[:100]}...")

            # Build context-aware system prompt
            system_prompt = PromptBuilder.build_conversation_prompt(CONVERSATION_SYSTEM_PROMPT, state)
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{message}")
            ])
            chain = prompt | self.llm

            # Call LLM for conversation with context
            response = await chain.ainvoke({"message": user_message})
            logger.info(f"LLM response received: {response.content[:100]}...")

            # Create response message
            assistant_message = ConversationMessage(
                role="assistant",
                content=response.content,
                timestamp=datetime.now().isoformat()
            )

            logger.info(f"Conversation agent responded: {response.content[:100]}")

            return {
                **state,
                "messages": state["messages"] + [assistant_message],
                "last_action": "conversation",
                "last_result": {"status": "success"}
            }

        except Exception as e:
            logger.error(f"Error in conversation agent: {str(e)}")
            error_message = ConversationMessage(
                role="assistant",
                content="I'm having trouble processing that. Could you rephrase your question?",
                timestamp=datetime.now().isoformat()
            )

            return {
                **state,
                "messages": state["messages"] + [error_message],
                "last_action": "conversation",
                "last_result": {"status": "error"},
                "error_message": str(e)
            }
