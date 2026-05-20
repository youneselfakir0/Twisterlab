import asyncio
import socket
import httpx
import redis
from pathlib import Path
from sqlalchemy import text

# ANSI colors for beautiful terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_status(component: str, success: bool, details: str):
    icon = "OK" if success else "ERR"
    color = GREEN if success else RED
    try:
        symbol = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
        print(f"  {symbol} {BOLD}{component:<15}{RESET} : {color}{details}{RESET}")
    except UnicodeEncodeError:
        print(f"  [{icon}] {BOLD}{component:<15}{RESET} : {color}{details}{RESET}")


async def check_database() -> bool:
    try:
        from twisterlab.database.manager import db_manager
        from sqlalchemy import select
        from twisterlab.database.models.resilience import CircuitBreaker
        
        async with db_manager.session() as session:
            # Simple select to verify database connection
            result = await session.execute(text("SELECT 1"))
            val = result.scalar()
            if val == 1:
                # Test querying a table
                try:
                    stmt = select(CircuitBreaker).limit(1)
                    await session.execute(stmt)
                    print_status("PostgreSQL", True, "Connected & Resilience schemas verified")
                    return True
                except Exception as table_ex:
                    print_status("PostgreSQL", True, f"Connected but schemas missing: {table_ex}")
                    return True
            else:
                print_status("PostgreSQL", False, "Connected but returned unexpected result")
                return False
    except Exception as e:
        print_status("PostgreSQL", False, f"Connection failed: {e}")
        return False


def check_redis() -> bool:
    try:
        from twisterlab.config.unified_settings import settings
        r = redis.Redis(
            host=settings.infra.redis_host,
            port=settings.infra.redis_port,
            password=settings.infra.redis_password,
            socket_timeout=2.0
        )
        if r.ping():
            print_status("Redis Cache", True, f"Connected ({settings.infra.redis_host}:{settings.infra.redis_port})")
            return True
        else:
            print_status("Redis Cache", False, "Ping failed")
            return False
    except Exception as e:
        print_status("Redis Cache", False, f"Connection failed: {e}")
        return False


async def check_llm() -> bool:
    try:
        from twisterlab.config.unified_settings import settings
        url = settings.infra.ollama_base_url
        model = settings.infra.ollama_model
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{url}/api/tags")
            if response.status_code == 200:
                models = [m.get("name") for m in response.json().get("models", [])]
                if model in models or any(model in m for m in models):
                    print_status("Ollama/Cortex", True, f"Connected. Target model '{model}' is available.")
                else:
                    avail = ", ".join(models) or "None"
                    print_status("Ollama/Cortex", True, f"Connected, but target model '{model}' not found. Available: [{avail}]")
                return True
            else:
                print_status("Ollama/Cortex", False, f"Ollama returned HTTP {response.status_code}")
                return False
    except Exception as e:
        print_status("Ollama/Cortex", False, f"Failed to connect to LLM: {e}")
        return False


def check_kucoin() -> bool:
    try:
        import ccxt
        from twisterlab.config.unified_settings import settings
        
        # Test public API first
        exchange_class = ccxt.kucoin
        exchange = exchange_class({
            'apiKey': settings.trading.kucoin_api_key or None,
            'secret': settings.trading.kucoin_secret or None,
            'password': settings.trading.kucoin_passphrase or None,
            'enableRateLimit': True,
        })
        
        if settings.trading.kucoin_is_sandbox:
            exchange.set_sandbox_mode(True)
            
        markets = exchange.fetch_markets()
        if len(markets) > 0:
            auth_str = "Authenticated" if settings.trading.kucoin_api_key else "Public only"
            mode_str = "Sandbox" if settings.trading.kucoin_is_sandbox else "Live"
            print_status("KuCoin API", True, f"Connected ({mode_str}, {auth_str}, {len(markets)} markets loaded)")
            return True
        else:
            print_status("KuCoin API", False, "Failed to retrieve market list")
            return False
    except Exception as e:
        print_status("KuCoin API", False, f"CCXT validation failed: {e}")
        return False


def check_port() -> bool:
    # Check if local port 8000 is occupied (gateway running)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 8000))
        print_status("Local Port 8000", True, "Free (Gateway is currently offline)")
        s.close()
        return True
    except socket.error:
        print_status("Local Port 8000", True, "In use (Gateway is online)")
        s.close()
        return True


async def run_doctor():
    try:
        print("\n" + "=" * 60)
        print(f"{BOLD}{CYAN}🔍 TwisterLab System Doctor Diagnostic{RESET}")
        print("=" * 60)
    except UnicodeEncodeError:
        print("\n" + "=" * 60)
        print(f"{BOLD}{CYAN}[Doctor] TwisterLab System Diagnostic{RESET}")
        print("=" * 60)
        
    print("Checking dependencies and connectivity...")
    print("-" * 60)
    
    db_ok = await check_database()
    redis_ok = check_redis()
    llm_ok = await check_llm()
    kucoin_ok = check_kucoin()
    port_ok = check_port()
    
    print("-" * 60)
    all_ok = db_ok and redis_ok and llm_ok and kucoin_ok
    if all_ok:
        try:
            print(f"{BOLD}{GREEN}🎉 System Status: HEALTHY! All components operational.{RESET}")
        except UnicodeEncodeError:
            print(f"{BOLD}{GREEN}[HEALTHY] System Status: HEALTHY! All components operational.{RESET}")
    else:
        try:
            print(f"{BOLD}{YELLOW}⚠ System Status: DEGRADED. Check details above to troubleshoot.{RESET}")
        except UnicodeEncodeError:
            print(f"{BOLD}{YELLOW}[DEGRADED] System Status: DEGRADED. Check details above to troubleshoot.{RESET}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_doctor())
