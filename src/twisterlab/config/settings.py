from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    app_name: str = "TwisterLab"
    app_version: str = "4.0.0"
    debug: bool = False

    # Database settings
    database_url: str = "sqlite+aiosqlite:///twisterlab.db"
    redis_url: str = "redis://localhost:6379/0"

    # Security settings
    secret_key: str = "dev_secret_key_change_me"

    # Notion Integration
    notion_token: Optional[str] = None
    notion_default_database_id: Optional[str] = None

    # n8n Integration
    n8n_api_key: Optional[str] = None
    n8n_base_url: str = "http://192.168.0.30:5678"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore" # Important for Pydantic V2 to ignore extra .env vars
    }
