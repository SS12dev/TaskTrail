"""Task tools, exercised through MCPServer.call_tool (real schema validation
+ registration, mocked HTTP underneath).
"""

from __future__ import annotations

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from tasktrail_mcp.server import mcp

from .conftest import json_response

pytestmark = pytest.mark.usefixtures("patched_client")

SAMPLE_TASK = {
    "id": "t1",
    "userId": "u1",
    "title": "Buy milk",
    "description": "",
    "status": "todo",
    "priority": "high",
    "dueDate": None,
    "tags": ["errand"],
    "projectId": None,
    "parentTaskId": None,
    "position": 0,
    "isRecurring": False,
    "recurrenceRule": None,
    "completedAt": None,
    "createdAt": "2026-08-01T00:00:00Z",
    "updatedAt": "2026-08-01T00:00:00Z",
}


async def test_create_task_posts_expected_body(patched_client):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/tasks/"
        return json_response(201, SAMPLE_TASK)

    patched_client.set_handler(handler)
    result = await mcp.call_tool("tasktrail_create_task", {"title": "Buy milk"})
    assert not result.is_error
    assert result.structured_content["id"] == "t1"


async def test_list_tasks_default_markdown(patched_client):
    patched_client.set_handler(
        lambda r: json_response(200, {"tasks": [SAMPLE_TASK], "total": 1})
    )
    result = await mcp.call_tool("tasktrail_list_tasks", {})
    text = result.content[0].text
    assert "Buy milk" in text
    assert "t1" in text


async def test_list_tasks_json_format_returns_full_objects(patched_client):
    patched_client.set_handler(
        lambda r: json_response(200, {"tasks": [SAMPLE_TASK], "total": 1})
    )
    result = await mcp.call_tool(
        "tasktrail_list_tasks", {"response_format": "json"}
    )
    assert result.structured_content["result"] == [SAMPLE_TASK]


async def test_list_tasks_empty_shows_friendly_message(patched_client):
    patched_client.set_handler(lambda r: json_response(200, {"tasks": [], "total": 0}))
    result = await mcp.call_tool("tasktrail_list_tasks", {})
    assert "No tasks match" in result.content[0].text


async def test_update_task_omits_unset_fields(patched_client):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json as jsonlib

        captured["body"] = jsonlib.loads(request.content)
        return json_response(200, {**SAMPLE_TASK, "status": "done"})

    patched_client.set_handler(handler)
    await mcp.call_tool("tasktrail_update_task", {"task_id": "t1", "status": "done"})
    assert captured["body"] == {"status": "done"}


async def test_delete_task_confirms_by_id(patched_client):
    patched_client.set_handler(lambda r: httpx.Response(204))
    result = await mcp.call_tool("tasktrail_delete_task", {"task_id": "t1"})
    assert "t1" in result.content[0].text
    assert "deleted" in result.content[0].text


async def test_get_task_not_found_raises_actionable_error(patched_client):
    patched_client.set_handler(lambda r: httpx.Response(404))
    with pytest.raises(ToolError, match="tasktrail_list_"):
        await mcp.call_tool("tasktrail_get_task", {"task_id": "missing"})
