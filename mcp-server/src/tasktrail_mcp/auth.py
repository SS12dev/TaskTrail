"""Firebase token management.

Exchanges a long-lived refresh token for short-lived ID tokens via the Firebase
Secure Token API, caching the ID token and refreshing ~5 minutes before expiry.
"""

import asyncio
import time

import httpx

from .config import settings

SECURE_TOKEN_URL = "https://securetoken.googleapis.com/v1/token"
REFRESH_MARGIN_SECONDS = 300


class TokenManager:
    """Caches a Firebase ID token, refreshing it before expiry."""

    def __init__(self) -> None:
        self._id_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        """Return a valid Firebase ID token.

        Uses TASKTRAIL_ID_TOKEN verbatim if set; otherwise exchanges the
        configured refresh token, caching the result.
        """
        if settings.tasktrail_id_token:
            return settings.tasktrail_id_token

        async with self._lock:
            if self._id_token and time.time() < self._expires_at - REFRESH_MARGIN_SECONDS:
                return self._id_token
            return await self._refresh()

    async def _refresh(self) -> str:
        settings.validate_auth()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                SECURE_TOKEN_URL,
                params={"key": settings.firebase_web_api_key},
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": settings.firebase_refresh_token,
                },
            )
        if response.status_code != 200:
            raise RuntimeError(
                "Firebase token refresh failed "
                f"(HTTP {response.status_code}): {response.text[:200]}. "
                "The refresh token may be revoked — re-run scripts/get_refresh_token.py."
            )
        payload = response.json()
        self._id_token = payload["id_token"]
        self._expires_at = time.time() + int(payload.get("expires_in", 3600))
        return self._id_token


token_manager = TokenManager()
