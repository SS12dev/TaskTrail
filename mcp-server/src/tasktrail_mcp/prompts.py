"""Prompt templates — pre-built instructions that steer the client's LLM to
use the CRUD tools in a particular workflow. These don't call the API
themselves; they return a user message telling the model what to do next.
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer


def register(mcp: MCPServer) -> None:
    @mcp.prompt(
        name="daily_standup",
        description="Summarize today's due/overdue tasks and propose a plan for the day.",
    )
    def daily_standup() -> str:
        return (
            "Call tasktrail_get_today_tasks to see what's due today, overdue, or "
            "high/urgent priority. Then:\n"
            "1. Summarize it in a short standup format: what's overdue, what's due "
            "today, what's high priority.\n"
            "2. Propose a realistic order to tackle today's items, considering "
            "priority and estimated effort implied by the task descriptions.\n"
            "3. Flag anything that looks stalled (no due date, sitting in "
            "in_progress) so I can decide whether to reschedule or drop it."
        )

    @mcp.prompt(
        name="weekly_review",
        description="Review completed vs. open tasks and surface stalled work.",
    )
    def weekly_review() -> str:
        return (
            "Call tasktrail_list_tasks with includeCompleted=True to get the full "
            "picture, and tasktrail_list_projects for project context. Then:\n"
            "1. Summarize what got done this period vs. what's still open, grouped "
            "by project.\n"
            "2. Call out tasks that have been in todo or in_progress a long time "
            "with no due date — these are candidates to reprioritize, "
            "reschedule, or archive.\n"
            "3. Suggest 2-3 concrete next actions for the coming week."
        )

    @mcp.prompt(
        name="plan_project",
        description="Break a goal description into a project and an initial set of tasks.",
    )
    def plan_project(project_description: str) -> str:
        return (
            f"Goal: {project_description}\n\n"
            "Break this into a TaskTrail project:\n"
            "1. Call tasktrail_create_project with a concise name and description "
            "capturing the goal.\n"
            "2. Decompose the goal into concrete tasks (aim for tasks that are "
            "independently actionable in under a day each). For each, call "
            "tasktrail_create_task with the new project's id, a clear title, "
            "sensible priority, and a dueDate only if there's a real deadline "
            "signal in the goal — don't invent dates.\n"
            "3. Show me the resulting task list and ask if the breakdown or "
            "priorities need adjusting before we're done."
        )
