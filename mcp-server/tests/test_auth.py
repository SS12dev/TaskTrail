"""TokenManager: caching, refresh, and the TASKTRAIL_ID_TOKEN escape hatch."""

from __future__ import annotations

import time

import httpx
import pytest

from tasktrail_mcp.auth import TokenManager
from tasktrail_mcp.config import settings


@pytest.fixture(autouse=True)
def clean_settings(monkeypatch: pytest.MonkeyPatch):
    """Every test starts from a known-empty auth config."""
    monkeypatch.setattr(settings, "tasktrail_id_token", None)
    monkeypatch.setattr(settings, "firebase_web_api_key", None)
    monkeypatch.setattr(settings, "firebase_refresh_token", None)


def patch_secure_token_client(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    from tasktrail_mcp import auth as auth_module

    real_async_client = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs.pop("timeout", None)
        return real_async_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(auth_module.httpx, "AsyncClient", fake_async_client)


async def test_id_token_escape_hatch_skips_refresh(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "tasktrail_id_token", "raw-token")
    manager = TokenManager()
    assert await manager.get_token() == "raw-token"


async def test_refresh_caches_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "firebase_web_api_key", "key")
    monkeypatch.setattr(settings, "firebase_refresh_token", "refresh")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"id_token": "id-1", "expires_in": "3600"})

    patch_secure_token_client(monkeypatch, handler)
    manager = TokenManager()

    first = await manager.get_token()
    second = await manager.get_token()

    assert first == second == "id-1"
    assert calls["n"] == 1  # second call served from cache


async def test_refresh_happens_again_near_expiry(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "firebase_web_api_key", "key")
    monkeypatch.setattr(settings, "firebase_refresh_token", "refresh")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"id_token": f"id-{calls['n']}", "expires_in": "3600"})

    patch_secure_token_client(monkeypatch, handler)
    manager = TokenManager()

    await manager.get_token()
    # Simulate the cached token being within the refresh margin of expiry.
    manager._expires_at = time.time() + 60  # less than REFRESH_MARGIN_SECONDS (300)

    second = await manager.get_token()
    assert second == "id-2"
    assert calls["n"] == 2


async def test_refresh_failure_raises_actionable_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "firebase_web_api_key", "key")
    monkeypatch.setattr(settings, "firebase_refresh_token", "revoked")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="INVALID_REFRESH_TOKEN")

    patch_secure_token_client(monkeypatch, handler)
    manager = TokenManager()

    with pytest.raises(RuntimeError, match="get_refresh_token.py"):
        await manager.get_token()


async def test_missing_config_raises_before_any_request(monkeypatch: pytest.MonkeyPatch):
    manager = TokenManager()
    with pytest.raises(RuntimeError, match="not configured"):
        await manager.get_token()
