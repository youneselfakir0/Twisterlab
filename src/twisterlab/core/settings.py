"""
TwisterLab Settings Module.

Loads configuration from environment variables with sensible defaults.
Supports multiple environments: development, staging, production.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: str = Field(default="development", description="Current environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="Number of API workers")
    api_reload: bool = Field(default=False, description="Enable auto-reload")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./twisterlab.db",
        description="Database connection URL",
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # Redis
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for signing tokens",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(
        default=60, description="JWT expiration in minutes"
    )

    # Ollama
    ollama_host: str = Field(
        default="http://localhost:11434", description="Ollama host URL"
    )
    ollama_model: str = Field(default="llama3.2", description="Default Ollama model")

    # MCP Server
    mcp_server_name: str = Field(default="twisterlab", description="MCP server name")
    mcp_server_version: str = Field(default="0.1.0", description="MCP server version")

    # CORS
    cors_origins: str = Field(default="*", description="Allowed CORS origins")

    # Monitoring
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus")
    prometheus_port: int = Field(default=9090, description="Prometheus port")

    # Feature Flags
    feature_browser_automation: bool = Field(
        default=True, description="Enable browser automation"
    )
    feature_mcp_integration: bool = Field(
        default=True, description="Enable MCP integration"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return self.environment.lower() == "staging"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Convenience function to load environment-specific config
def load_environment_config(env: str = None) -> None:
    """
    Load environment-specific configuration file.

    Args:
        env: Environment name (development, staging, production).
             Defaults to ENVIRONMENT env var or 'development'.
    """
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")

    config_dir = Path(__file__).parent.parent.parent / "config" / "environments"
    env_file = config_dir / f"{env}.env"

    if env_file.exists():
        from dotenv import load_dotenv

        load_dotenv(env_file)


# Export
__all__ = ["Settings", "get_settings", "load_environment_config"]
