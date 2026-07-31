"""Configuration loaded from environment variables (set via MCP client config)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """TaskTrail MCP server settings.

    Auth: either provide firebase_web_api_key + firebase_refresh_token
    (recommended — tokens auto-refresh), or a raw tasktrail_id_token for
    quick testing (expires after ~1 hour).
    """

    tasktrail_api_url: str = "http://localhost:8000"

    firebase_web_api_key: str | None = None
    firebase_refresh_token: str | None = None
    tasktrail_id_token: str | None = None

    request_timeout_seconds: float = 30.0
    agent_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    def validate_auth(self) -> None:
        """Fail fast with an actionable message if auth is not configured."""
        if self.tasktrail_id_token:
            return
        if not (self.firebase_web_api_key and self.firebase_refresh_token):
            raise RuntimeError(
                "TaskTrail MCP auth is not configured. Set FIREBASE_WEB_API_KEY and "
                "FIREBASE_REFRESH_TOKEN (run mcp-server/scripts/get_refresh_token.py to "
                "obtain one), or set TASKTRAIL_ID_TOKEN for quick testing."
            )


settings = Settings()
