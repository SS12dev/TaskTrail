# Fix supervisor agent prompt variable issue
with open('app/agents/supervisor_agent.py', 'r') as f:
    content = f.read()

# Replace the problematic section
old_code = '''            # Get context-aware system prompt
            system_prompt = self._get_system_prompt(state)

            # Create prompt with context
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "User message: {message}\\n\\nRecent context: {context}\\n\\nRoute this request.")
            ])'''

new_code = '''            # Build user context inline to avoid template variable issues
            user_context = ""
            if state.get("detailed_user_context"):
                ctx = state["detailed_user_context"]
                try:
                    ts_fmt = ctx["current_timestamp"].strftime('%B %d, %Y at %I:%M %p')
                except Exception:
                    ts_fmt = str(ctx.get("current_timestamp"))
                user_context = (
                    f"Current Time: {ts_fmt}\\n"
                    f"Timezone: {ctx.get('timezone', 'UTC')} (Day: {ctx.get('day_of_week', 'Unknown')}, "
                    f"Time: {ctx.get('time_of_day', 'Unknown')})"
                )
            
            # Build complete system prompt (no template variables)
            system_prompt = f"{SUPERVISOR_SYSTEM_PROMPT}\\n\\n**User Context:**\\n{user_context}"

            # Create prompt with only message and context variables
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "User message: {message}\\n\\nRecent context: {context}\\n\\nRoute this request.")
            ])'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('app/agents/supervisor_agent.py', 'w') as f:
        f.write(content)
    print("✓ Updated supervisor_agent.py")
else:
    print("❌ Could not find code to replace")
