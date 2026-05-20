import os
from pathlib import Path

# ANSI colors for beautiful terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(title: str):
    print("\n" + "=" * 60)
    try:
        print(f"{BOLD}{CYAN}  {title}{RESET}")
    except UnicodeEncodeError:
        cleaned = title.encode('ascii', 'ignore').decode('ascii')
        print(f"{BOLD}{CYAN}  {cleaned}{RESET}")
    print("=" * 60)


def ask_question(question: str, default: str) -> str:
    prompt = f"{YELLOW}{question}{RESET} [{default}]: "
    res = input(prompt).strip()
    return res if res else default


def ask_bool(question: str, default: bool) -> bool:
    default_str = "Y/n" if default else "y/N"
    prompt = f"{YELLOW}{question}{RESET} ({default_str}): "
    res = input(prompt).strip().lower()
    if not res:
        return default
    return res.startswith("y")


def run_onboard():
    print_header("TwisterLab Onboarding Setup Wizard")
    print("This wizard will help you configure the core settings for TwisterLab.")
    print("Configurations will be saved to your local '.env' file.")

    # Load existing env if available
    from twisterlab.config.unified_settings import settings

    # 1. CORE SETTINGS
    print_header("1. Core Settings")
    debug = ask_bool("Enable debug mode?", settings.core.debug)
    secret_key = ask_question("Application Secret Key?", settings.core.secret_key)

    # 2. INFRASTRUCTURE SETTINGS
    print_header("2. Database & Cache Infrastructure")
    pg_host = ask_question("PostgreSQL Hostname?", settings.infra.postgres_host)
    pg_port = int(ask_question("PostgreSQL Port?", str(settings.infra.postgres_port)))
    pg_user = ask_question("PostgreSQL Username?", settings.infra.postgres_user)
    pg_pass = ask_question("PostgreSQL Password?", settings.infra.postgres_password)
    pg_db = ask_question("PostgreSQL Database Name?", settings.infra.postgres_db)

    redis_host = ask_question("Redis Hostname?", settings.infra.redis_host)
    redis_port = int(ask_question("Redis Port?", str(settings.infra.redis_port)))
    redis_pass = ask_question("Redis Password?", settings.infra.redis_password or "")

    # 3. AI & ORCHESTRATION SETTINGS
    print_header("3. LLM (Cortex) & Integrations")
    ollama_url = ask_question("Cortex/Ollama API URL?", settings.infra.ollama_base_url)
    ollama_model = ask_question("Default LLM Model?", settings.infra.ollama_model)

    notion_token = ask_question("Notion Integration Token?", settings.infra.notion_token or "")
    notion_db = ask_question("Notion Default Database ID?", settings.infra.notion_default_database_id or "")

    # 4. TRADING SETTINGS
    print_header("4. Trading & Risk Controls")
    kucoin_key = ask_question("KuCoin API Key?", settings.trading.kucoin_api_key)
    kucoin_secret = ask_question("KuCoin API Secret?", settings.trading.kucoin_secret)
    kucoin_pass = ask_question("KuCoin API Passphrase?", settings.trading.kucoin_passphrase)
    kucoin_sandbox = ask_bool("Enable KuCoin Sandbox?", settings.trading.kucoin_is_sandbox)

    max_notional = float(ask_question("Maximum order size (USD)?", str(settings.trading.max_notional_usd)))
    max_daily_loss = float(ask_question("Maximum daily loss (USD)?", str(settings.trading.max_daily_loss_usd)))
    manual_approval = ask_bool("Require manual approval for trades?", settings.trading.manual_approval_required)

    # Compile the .env string
    env_content = f"""# TwisterLab Generated Environment Variables
# Generated on: {Path('.').resolve()}

# Core
CORE__DEBUG={str(debug).lower()}
CORE__SECRET_KEY={secret_key}

# Postgres Database
INFRA__POSTGRES_HOST={pg_host}
INFRA__POSTGRES_PORT={pg_port}
INFRA__POSTGRES_USER={pg_user}
INFRA__POSTGRES_PASSWORD={pg_pass}
INFRA__POSTGRES_DB={pg_db}

# Redis Cache
INFRA__REDIS_HOST={redis_host}
INFRA__REDIS_PORT={redis_port}
INFRA__REDIS_PASSWORD={redis_pass}

# AI (Ollama/Cortex)
INFRA__OLLAMA_BASE_URL={ollama_url}
INFRA__OLLAMA_MODEL={ollama_model}

# Notion API
INFRA__NOTION_TOKEN={notion_token}
INFRA__NOTION_DEFAULT_DATABASE_ID={notion_db}

# Trading Credentials & Risk
TRADING__KUCOIN_API_KEY={kucoin_key}
TRADING__KUCOIN_SECRET={kucoin_secret}
TRADING__KUCOIN_PASSPHRASE={kucoin_pass}
TRADING__KUCOIN_IS_SANDBOX={str(kucoin_sandbox).lower()}
TRADING__MAX_NOTIONAL_USD={max_notional}
TRADING__MAX_DAILY_LOSS_USD={max_daily_loss}
TRADING__MANUAL_APPROVAL_REQUIRED={str(manual_approval).lower()}
"""

    env_path = Path(".env")
    env_path.write_text(env_content, encoding="utf-8")

    print("\n" + "=" * 60)
    try:
        print(f"{BOLD}{GREEN}🎉 Configuration successfully saved to {env_path.absolute()}{RESET}")
    except UnicodeEncodeError:
        print(f"{BOLD}{GREEN}[OK] Configuration successfully saved to {env_path.absolute()}{RESET}")
    print(f"To verify your connection settings, run: {BOLD}twisterlab doctor{RESET}")
    print("=" * 60 + "\n")
