"""Thin async HTTP client for the TaskTrail REST API.

Never talks to Firestore or backend code directly — this is a pure HTTP client,
per the contract in the root CLAUDE.md. All requests carry a Firebase ID token
obtained from `auth.token_manager`.
"""

from __future__ import annotations

from typing import Any

import httpx

from .auth import token_manager
from .config import settings


class TaskTrailAPIError(RuntimeError):
    """Raised when the TaskTrail API returns an error.

    The message is written to be shown directly to an LLM/user — never a raw
    traceback or stack dump.
    """


class TaskTrailClient:
    """Async client for `/api/v1/*` endpoints, with actionable error mapping."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=f"{settings.tasktrail_api_url.rstrip('/')}/api/v1",
            timeout=settings.request_timeout_seconds,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> TaskTrailClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    # -- core request/error mapping -----------------------------------------

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Make an authenticated request and return the decoded JSON body.

        Returns None for 204 No Content responses. Raises TaskTrailAPIError with
        an actionable message on any failure — connection, auth, or HTTP status.
        """
        try:
            token = await token_manager.get_token()
        except RuntimeError as exc:
            raise TaskTrailAPIError(str(exc)) from exc

        headers = {"Authorization": f"Bearer {token}"}
        # Drop params with a None value — FastAPI/Query treats an explicit
        # "None" string differently from an omitted param.
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        try:
            response = await self._client.request(
                method,
                path,
                json=json,
                params=clean_params or None,
                headers=headers,
                timeout=timeout or settings.request_timeout_seconds,
            )
        except httpx.ConnectError as exc:
            raise TaskTrailAPIError(
                f"Backend unreachable at {settings.tasktrail_api_url} — "
                "is the FastAPI server running? (`uvicorn app.main:app --reload --port 8000`)"
            ) from exc
        except httpx.TimeoutException as exc:
            effective_timeout = timeout or settings.request_timeout_seconds
            raise TaskTrailAPIError(
                f"Request to {path} timed out after {effective_timeout}s. The backend may "
                "be slow or unresponsive — try again, or check backend logs."
            ) from exc

        if response.status_code == 401:
            raise TaskTrailAPIError(
                "Authentication failed — the Firebase refresh token is invalid or expired. "
                "Re-run `uv run python scripts/get_refresh_token.py` and update "
                "FIREBASE_REFRESH_TOKEN."
            )
        if response.status_code == 404:
            raise TaskTrailAPIError(
                f"Not found ({method} {path}) — verify the ID via the matching "
                "tasktrail_list_* or tasktrail_get_* tool; it may have been deleted."
            )
        if response.status_code == 422:
            detail = self._extract_validation_detail(response)
            raise TaskTrailAPIError(f"Validation error: {detail}")
        if response.status_code >= 400:
            raise TaskTrailAPIError(
                f"TaskTrail API error {response.status_code} on {method} {path}: "
                f"{response.text[:300]}"
            )

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    @staticmethod
    def _extract_validation_detail(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return response.text[:300]
        detail = body.get("detail")
        if isinstance(detail, list):
            parts = []
            for item in detail:
                loc = ".".join(str(p) for p in item.get("loc", []) if p != "body")
                parts.append(f"{loc}: {item.get('msg', 'invalid')}")
            return "; ".join(parts) or str(detail)
        return str(detail) if detail is not None else response.text[:300]

    # -- convenience verbs -----------------------------------------------------

    async def get(self, path: str, **kw: Any) -> Any:
        return await self.request("GET", path, **kw)

    async def post(self, path: str, **kw: Any) -> Any:
        return await self.request("POST", path, **kw)

    async def patch(self, path: str, **kw: Any) -> Any:
        return await self.request("PATCH", path, **kw)

    async def delete(self, path: str, **kw: Any) -> Any:
        return await self.request("DELETE", path, **kw)


# Module-level singleton — one connection pool for the life of the server process.
client = TaskTrailClient()
