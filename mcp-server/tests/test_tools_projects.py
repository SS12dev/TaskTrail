"""Project tools, exercised through MCPServer.call_tool."""

from __future__ import annotations

import json

import httpx
import pytest

from tasktrail_mcp.server import mcp

from .conftest import json_response

pytestmark = pytest.mark.usefixtures("patched_client")

SAMPLE_PROJECT = {
    "id": "p1",
    "userId": "u1",
    "name": "Q3 Launch",
    "description": "",
    "color": "#3B82F6",
    "icon": "Folder",
    "isArchived": False,
    "taskCount": 3,
    "createdAt": "2026-08-01T00:00:00Z",
    "updatedAt": "2026-08-01T00:00:00Z",
}


async def test_create_project_defaults(patched_client):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return json_response(201, SAMPLE_PROJECT)

    patched_client.set_handler(handler)
    await mcp.call_tool("tasktrail_create_project", {"name": "Q3 Launch"})
    assert captured["body"]["color"] == "#3B82F6"
    assert captured["body"]["icon"] == "Folder"


async def test_list_projects_markdown_shows_task_count(patched_client):
    patched_client.set_handler(
        lambda r: json_response(200, {"projects": [SAMPLE_PROJECT], "total": 1})
    )
    result = await mcp.call_tool("tasktrail_list_projects", {})
    text = result.content[0].text
    assert "Q3 Launch" in text
    assert "3 task(s)" in text


async def test_update_project_archive(patched_client):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return json_response(200, {**SAMPLE_PROJECT, "isArchived": True})

    patched_client.set_handler(handler)
    await mcp.call_tool(
        "tasktrail_update_project", {"project_id": "p1", "isArchived": True}
    )
    assert captured["body"] == {"isArchived": True}


async def test_delete_project_confirms_by_id(patched_client):
    patched_client.set_handler(lambda r: httpx.Response(204))
    result = await mcp.call_tool("tasktrail_delete_project", {"project_id": "p1"})
    assert "p1" in result.content[0].text
