"""TaskTrailClient: HTTP verbs, status-code -> error-message mapping."""

from __future__ import annotations

import httpx
import pytest

from tasktrail_mcp.client import TaskTrailAPIError

from .conftest import json_response, make_client


@pytest.mark.usefixtures("fixed_token")
class TestSuccessPaths:
    async def test_get_returns_json_body(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert request.url.path == "/api/v1/tasks/"
            return json_response(200, {"tasks": [], "total": 0})

        client = make_client(handler)
        result = await client.get("/tasks/")
        assert result == {"tasks": [], "total": 0}

    async def test_delete_204_returns_none(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        client = make_client(handler)
        assert await client.delete("/tasks/abc") is None

    async def test_sends_bearer_token(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["auth"] = request.headers.get("authorization")
            return json_response(200, {})

        client = make_client(handler)
        await client.get("/tasks/today")
        assert seen["auth"] == "Bearer fake-id-token"

    async def test_none_params_are_dropped(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "status" not in request.url.params
            assert request.url.params["includeCompleted"] == "false"
            return json_response(200, {"tasks": [], "total": 0})

        client = make_client(handler)
        await client.get("/tasks/", params={"status": None, "includeCompleted": False})


@pytest.mark.usefixtures("fixed_token")
class TestErrorMapping:
    async def test_401_message_mentions_refresh_token(self):
        client = make_client(lambda r: httpx.Response(401))
        with pytest.raises(TaskTrailAPIError, match="refresh token"):
            await client.get("/tasks/")

    async def test_404_message_suggests_list_tool(self):
        client = make_client(lambda r: httpx.Response(404))
        with pytest.raises(TaskTrailAPIError, match="tasktrail_list_"):
            await client.get("/tasks/missing")

    async def test_422_surfaces_field_detail(self):
        body = {
            "detail": [
                {"loc": ["body", "title"], "msg": "field required", "type": "missing"}
            ]
        }
        client = make_client(lambda r: json_response(422, body))
        with pytest.raises(TaskTrailAPIError, match="title: field required"):
            await client.post("/tasks/", json={})

    async def test_500_includes_status_and_body(self):
        client = make_client(lambda r: httpx.Response(500, text="boom"))
        with pytest.raises(TaskTrailAPIError, match="500"):
            await client.get("/tasks/")

    async def test_connect_error_message_is_actionable(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        client = make_client(handler)
        with pytest.raises(TaskTrailAPIError, match="Backend unreachable"):
            await client.get("/tasks/")

    async def test_timeout_message_is_actionable(self):
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("slow")

        client = make_client(handler)
        with pytest.raises(TaskTrailAPIError, match="timed out"):
            await client.get("/tasks/")


async def test_auth_failure_before_request_is_wrapped(monkeypatch: pytest.MonkeyPatch):
    """If TokenManager can't even get a token, that should surface as a
    TaskTrailAPIError too, not a raw RuntimeError, so MCP clients see a
    consistent error shape."""
    from tasktrail_mcp import auth

    async def _fail() -> str:
        raise RuntimeError("no auth configured")

    monkeypatch.setattr(auth.token_manager, "get_token", _fail)
    client = make_client(lambda r: httpx.Response(200))
    with pytest.raises(TaskTrailAPIError, match="no auth configured"):
        await client.get("/tasks/")
