"""
Prompt Builder Utility for Agents

This module provides utilities to build context-aware system prompts
for all agents with accurate user time and timezone information.
"""

from app.models.agent_state import AgentState
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Utility class for building context-aware prompts."""
    
    @staticmethod
    def get_user_context_string(state: AgentState) -> str:
        """
        Build a formatted user context string from AgentState.
        
        Args:
            state: AgentState containing detailed_user_context
            
        Returns:
            Formatted context string for inclusion in prompts
        """
        if not state.get("detailed_user_context"):
            return ""
        
        ctx = state["detailed_user_context"]
        if isinstance(ctx.get("current_timestamp"), datetime):
            timestamp_str = ctx["current_timestamp"].strftime('%B %d, %Y at %I:%M %p')
        else:
            timestamp_str = str(ctx.get("current_timestamp"))
        
        return f"""IMPORTANT USER CONTEXT:
- **Current Date & Time**: {timestamp_str}
- **Timezone**: {ctx.get('timezone', 'UTC')}
- **Day of Week**: {ctx.get('day_of_week', 'Unknown')}
- **Time of Day**: {ctx.get('time_of_day', 'Unknown').capitalize()}

When interpreting relative dates and times, use this current time as the reference point."""
    
    @staticmethod
    def build_conversation_prompt(base_prompt: str, state: AgentState) -> str:
        """
        Build a conversation prompt with user context injected.
        
        Args:
            base_prompt: Base system prompt
            state: AgentState with user context
            
        Returns:
            Enhanced prompt with user context
        """
        context = PromptBuilder.get_user_context_string(state)
        if context:
            return f"{base_prompt}\n\n{context}"
        return base_prompt
    
    @staticmethod
    def build_executor_prompt(base_prompt: str, state: AgentState) -> str:
        """
        Build an executor prompt with precise date/time information.
        
        Args:
            base_prompt: Base system prompt
            state: AgentState with user context
            
        Returns:
            Enhanced prompt with date/time context for executor
        """
        context_str = PromptBuilder.get_user_context_string(state)
        
        if state.get("detailed_user_context"):
            ctx = state["detailed_user_context"]
            if isinstance(ctx.get("current_timestamp"), datetime):
                # Calculate specific dates for date parsing
                ts = ctx["current_timestamp"]
                today = ts.strftime('%Y-%m-%d')
                tomorrow = (ts.replace(day=ts.day + 1) if ts.day < 28 else ts.replace(month=ts.month + 1, day=1)).strftime('%Y-%m-%d')
                next_week = (ts.replace(day=ts.day + 7) if ts.day + 7 <= 31 else ts.replace(month=ts.month + 1, day=(ts.day + 7 - 31))).strftime('%Y-%m-%d')
                
                date_context = f"""
**Date References for Task Creation**:
- Today: {today}
- Tomorrow: {tomorrow}
- Next week: {next_week}

When you create tasks, use these ISO dates (YYYY-MM-DD format) or natural language that will be converted."""
                context_str += date_context
        
        if context_str:
            return f"{base_prompt}\n\n{context_str}"
        return base_prompt

    @staticmethod
    def build_query_prompt(base_prompt: str, state: AgentState) -> str:
        """
        Build a query prompt emphasizing timezone-aware interpretation of dates.

        Args:
            base_prompt: Base system prompt
            state: AgentState with user context

        Returns:
            Enhanced prompt with guidance for time-related queries
        """
        context = PromptBuilder.get_user_context_string(state)

        guidance = """
**Time Interpretation Guidance**:
- Interpret "today", "tomorrow", "this week" using the user's timezone.
- Use the current date/time above as the reference for filters.
- When summarizing results, mention counts and key deadlines.
"""

        if context:
            return f"{base_prompt}\n\n{context}\n\n{guidance}"
        return f"{base_prompt}\n\n{guidance}"

    @staticmethod
    def attach_memory_context(prompt: str, memory_context: str | None) -> str:
        """
        Optionally attach retrieved memory context to a prompt.
        """
        if memory_context:
            return f"{prompt}\n\nRelevant Memory:\n{memory_context}"
        return prompt
