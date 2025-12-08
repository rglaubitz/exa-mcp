"""Configuration management using pydantic-settings.

Handles environment variable loading and validation for the Exa MCP server.
"""

import sys
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        exa_api_key: API key for Exa AI (required)
        log_level: Logging level (default: INFO)
        debug: Enable debug mode (default: False)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    exa_api_key: str = Field(
        ...,
        description="API key for Exa AI from dashboard.exa.ai",
        json_schema_extra={"env": "EXA_API_KEY"},
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode for verbose logging",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Validated settings from environment variables.

    Raises:
        ValidationError: If required settings are missing or invalid.
    """
    return Settings()  # type: ignore[call-arg]


def validate_settings() -> bool:
    """Validate settings on startup.

    Returns:
        bool: True if settings are valid.

    Raises:
        SystemExit: If settings validation fails.
    """
    try:
        settings = get_settings()
        if not settings.exa_api_key:
            print("Error: EXA_API_KEY environment variable is required", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        return False
