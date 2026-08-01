"""Shared fixtures. Everything here is mocked — no real network calls, no
live TaskTrail backend required to run the suite.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest

from tasktrail_mcp.client import TaskTrailClient

Handler = Callable[[httpx.Request], httpx.Response]


def make_client(handler: Handler) -> TaskTrailClient:
    """Build a TaskTrailClient whose underlying transport is mocked."""
    trail_client = TaskTrailClient()
    trail_client._client = httpx.AsyncClient(
        base_url=trail_client._client.base_url,
        transport=httpx.MockTransport(handler),
    )
    return trail_client


def json_response(status_code: int, body: Any) -> httpx.Response:
    return httpx.Response(status_code, json=body)


@pytest.fixture
def fixed_token(monkeypatch: pytest.MonkeyPatch) -> str:
    """Skip real Firebase auth entirely — tools/client tests care about REST
    behavior, not token refresh (that's covered in test_auth.py)."""
    from tasktrail_mcp import auth

    async def _get_token() -> str:
        return "fake-id-token"

    monkeypatch.setattr(auth.token_manager, "get_token", _get_token)
    return "fake-id-token"


@pytest.fixture
def patched_client(monkeypatch: pytest.MonkeyPatch, fixed_token: str):
    """Patch the module-level `client` singleton used by tools/resources to
    route through a MockTransport controlled by the test. Returns a small
    controller object so tests can install per-test handlers.
    """
    import tasktrail_mcp.client as client_module

    state: dict[str, Handler] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        return state["handler"](request)

    mock = make_client(handler)
    monkeypatch.setattr(client_module, "client", mock)
    # tools/resources modules do `from ..client import client` at import time,
    # so also patch those already-bound references.
    for mod_name in (
        "tasktrail_mcp.tools.tasks",
        "tasktrail_mcp.tools.projects",
        "tasktrail_mcp.tools.agent",
        "tasktrail_mcp.resources",
    ):
        import importlib

        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        if hasattr(mod, "client"):
            monkeypatch.setattr(mod, "client", mock)

    class Controller:
        def set_handler(self, fn: Handler) -> None:
            state["handler"] = fn

    return Controller()
