from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    app_name: str = "TwisterLab"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database settings
    database_url: str = "sqlite+aiosqlite:///twisterlab_trader.db"
    redis_url: str = "redis://localhost:6379/0"

    # Security settings
    secret_key: str = "dev_secret_key_change_me"

    # PHASE 6: Live Broker Settings (KuCoin)
    kucoin_api_key: str = ""
    kucoin_secret: str = ""
    kucoin_passphrase: str = ""
    kucoin_is_sandbox: bool = False
    kucoin_market_type: str = "spot" # "spot" or "futures"

    # Notion Integration
    notion_token: Optional[str] = None
    notion_default_database_id: Optional[str] = None

    # n8n Integration
    n8n_api_key: Optional[str] = None
    n8n_base_url: str = "http://192.168.0.30:5678"

    # Execution Risk Guards
    trading_max_notional_usd: float = 5.0
    trading_max_daily_loss_usd: float = 50.0
    trading_max_total_exposure_usd: float = 50.0 # NEW: Global portfolio cap
    trading_allowed_symbols: list[str] = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
    trading_manual_approval_required: bool = True
    
    # PHASE 7: Stop Manager Settings
    trading_tsl_profit_activation_pct: float = 0.015 # Option B: 1.5% profit to activate TSL
    trading_tsl_distance_pct: float = 0.010 # 1.0% trailing distance
    trading_tsl_atr_multiplier: float = 1.5 # NEW: Phase 10 ATR-based TSL distance
    trading_stop_manager_polling_interval: int = 30 # 30-second loop

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore" # Important for Pydantic V2 to ignore extra .env vars
    }
