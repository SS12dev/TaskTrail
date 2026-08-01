"""Resources (read-only tasktrail:// snapshots) and prompts (message templates)."""

from __future__ import annotations

import httpx
import pytest

from tasktrail_mcp.server import mcp

from .conftest import json_response

pytestmark = pytest.mark.usefixtures("patched_client")


async def test_today_resource_renders_markdown(patched_client):
    patched_client.set_handler(
        lambda r: json_response(
            200,
            {
                "tasks": [
                    {
                        "id": "t1",
                        "title": "Ship release",
                        "status": "in_progress",
                        "priority": "urgent",
                        "dueDate": "2026-08-01T00:00:00Z",
                        "tags": [],
                        "projectId": None,
                    }
                ],
                "total": 1,
            },
        )
    )
    contents = await mcp.read_resource("tasktrail://today")
    contents = list(contents)
    assert len(contents) == 1
    assert "Ship release" in contents[0].content


async def test_today_resource_empty(patched_client):
    patched_client.set_handler(lambda r: json_response(200, {"tasks": [], "total": 0}))
    contents = list(await mcp.read_resource("tasktrail://today"))
    assert "Nothing due today" in contents[0].content


async def test_project_tasks_template_resource(patched_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["projectId"] == "p1"
        return json_response(200, {"tasks": [], "total": 0})

    patched_client.set_handler(handler)
    contents = list(await mcp.read_resource("tasktrail://projects/p1/tasks"))
    assert "p1" in contents[0].content


async def test_daily_standup_prompt_mentions_get_today_tool():
    result = await mcp.get_prompt("daily_standup")
    text = result.messages[0].content.text
    assert "tasktrail_get_today_tasks" in text


async def test_plan_project_prompt_includes_description():
    result = await mcp.get_prompt(
        "plan_project", {"project_description": "Launch the v2 mobile app"}
    )
    text = result.messages[0].content.text
    assert "Launch the v2 mobile app" in text
    assert "tasktrail_create_project" in text
