from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    These settings are automatically loaded from the .env file
    and provide type-safe access to configuration values.
    """

    # Environment configuration
    environment: str = "development"

    # Firebase configuration
    firebase_service_account_path: str

    # Frontend CORS configuration
    frontend_url: str = "http://localhost:5174"

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000

    # A2A Protocol Configuration
    a2a_agent_id: str = "tasktrail-multi-agent-v1"
    a2a_agent_name: str = "TaskTrail AI Assistant"
    a2a_service_endpoint: str = "http://localhost:8000/a2a/v1"
    a2a_enable_server: bool = True
    a2a_enable_client: bool = True

    # WebSocket Configuration
    websocket_enabled: bool = True
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 30
    websocket_max_connections_per_user: int = 5

    # External A2A Agents Configuration
    # Comma-separated list of external agent discovery URLs
    external_agents: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get settings instance (useful for dependency injection)

    Returns:
        Settings instance
    """
    return settings
