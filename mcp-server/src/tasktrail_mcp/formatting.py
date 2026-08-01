"""Markdown rendering for tasks/projects, so list tools return concise, readable
text by default instead of a raw JSON dump (which burns context and is harder
for an LLM to skim). `response_format="json"` bypasses this and returns the
full payload for callers that need every field.
"""

from __future__ import annotations

from typing import Any

_PRIORITY_MARK = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}
_STATUS_MARK = {"todo": "☐", "in_progress": "◐", "done": "☑", "archived": "🗄"}


def _short_date(value: str | None) -> str:
    if not value:
        return ""
    return value[:10]  # ISO datetime -> YYYY-MM-DD


def format_task_line(task: dict[str, Any]) -> str:
    """One task as a single markdown list line."""
    status = _STATUS_MARK.get(task.get("status", ""), "•")
    priority = _PRIORITY_MARK.get(task.get("priority", ""), "")
    due = _short_date(task.get("dueDate"))
    due_part = f" (due {due})" if due else ""
    project_part = f" [project:{task['projectId']}]" if task.get("projectId") else ""
    tags = task.get("tags") or []
    tags_part = f" #{' #'.join(tags)}" if tags else ""
    return (
        f"{status} {priority} **{task['title']}**{due_part}{project_part}{tags_part} "
        f"`id={task['id']}`"
    ).strip()


def format_task_list(tasks: list[dict[str, Any]], *, empty_message: str) -> str:
    if not tasks:
        return empty_message
    return "\n".join(f"- {format_task_line(t)}" for t in tasks)


def format_project_line(project: dict[str, Any]) -> str:
    archived = " (archived)" if project.get("isArchived") else ""
    count = project.get("taskCount", 0)
    return (
        f"**{project['name']}**{archived} — {count} task(s) "
        f"`id={project['id']}`"
    )


def format_project_list(projects: list[dict[str, Any]], *, empty_message: str) -> str:
    if not projects:
        return empty_message
    return "\n".join(f"- {format_project_line(p)}" for p in projects)
