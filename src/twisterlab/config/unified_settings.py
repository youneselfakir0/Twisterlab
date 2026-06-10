from __future__ import annotations
from pydantic import Field, HttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Union

class CoreSettings(BaseSettings):
    """Paramètres fondamentaux de l'application."""
    app_name: str = "TwisterLab"
    version: str = "4.0.0-stable"
    debug: bool = False
    secret_key: str = "insecure-default-change-me"
    jwt_secret_key: str = "jwt-secret-change-me"
    allowed_origins: List[str] = ["*"]
    rate_limit_per_minute: int = 500

class InfraSettings(BaseSettings):
    """Configuration de l'infrastructure et des services externes (Zéro IP)."""
    # Database (Usage du DNS interne par défaut)
    postgres_host: str = "postgres.twisterlab.svc.cluster.local"
    postgres_user: str = "twisterlab"
    postgres_password: str = "twisterlab"
    postgres_db: str = "twisterlab_prod"
    postgres_port: int = 5432

    # Redis
    redis_host: str = "redis.twisterlab.svc.cluster.local"
    redis_port: int = 6379
    redis_password: Optional[str] = None

    @field_validator("redis_port", "postgres_port", mode="before")
    @classmethod
    def _strip_k8s_service_env(cls, v: Union[str, int]) -> int:
        """Kubernetes injects REDIS_PORT/POSTGRES_PORT as 'tcp://host:port'.
        Strip the protocol prefix so pydantic can parse the integer."""
        if isinstance(v, str) and v.startswith("tcp://"):
            # Format: tcp://10.43.91.24:6379  →  6379
            return int(v.rsplit(":", 1)[-1])
        return int(v)

    # AI Services
    ollama_base_url: str = "http://ollama.twisterlab.svc.cluster.local:11434"
    ollama_model: str = "llama3.2:1b"
    
    # n8n
    n8n_url: str = "http://n8n.twisterlab.svc.cluster.local:5678"
    n8n_api_key: Optional[str] = None

    # Notion
    notion_token: Optional[str] = None
    notion_default_database_id: Optional[str] = None

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/0"

class TradingSettings(BaseSettings):
    """Configuration métier liée au trading et à l'exécution."""
    kucoin_api_key: str = ""
    kucoin_secret: str = ""
    kucoin_passphrase: str = ""
    kucoin_is_sandbox: bool = False
    
    # Risk Management
    max_notional_usd: float = 5.0
    max_daily_loss_usd: float = 50.0
    max_total_exposure_usd: float = 50.0
    allowed_symbols: List[str] = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    manual_approval_required: bool = True
    
    # Trailing Stop Loss (TSL)
    tsl_profit_activation_pct: float = 0.015
    tsl_distance_pct: float = 0.010
    stop_manager_polling_interval: int = 30

class Settings(BaseSettings):
    """Agrégateur principal des paramètres TwisterLab."""
    core: CoreSettings = CoreSettings()
    infra: InfraSettings = InfraSettings()
    trading: TradingSettings = TradingSettings()

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", # Permet d'injecter CORE__DEBUG=true
        env_file=".env",
        extra="ignore"
    )

# Singleton global pour injection simplifiée
settings = Settings()
