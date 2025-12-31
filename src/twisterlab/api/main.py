import sys
from pathlib import Path

# Add /app to sys.path to ensure twisterlab package is found
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Response as FastAPIResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Optional instrumentation (OpenTelemetry) - import lazily and gracefully
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    FastAPIInstrumentor = None

from .routes import agents, browser, mcp, system
from . import routes_mcp_real


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables if they are not present.
    # Import models module to ensure ORM models are registered with Base
    import twisterlab.database.models.agent  # noqa: F401
    from twisterlab.database.session import Base, engine

    # Create tables using an appropriate sync/async path depending on engine type
    try:
        if hasattr(engine, "begin"):
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            bind_engine = getattr(engine, "sync_engine", engine)
            Base.metadata.create_all(bind=bind_engine)
    except Exception:
        try:
            import logging

            logging.getLogger(__name__).exception("Failed to initialize DB tables")
        except Exception:
            pass
    
    # Initialize Agent Registry with all agents
    try:
        from twisterlab.agents.registry import AgentRegistry
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Initializing AgentRegistry...")
        registry = AgentRegistry()
        registry.initialize_agents()
        logger.info(f"AgentRegistry initialized with {len(registry._agents)} agents")
    except Exception as e:
        try:
            import logging
            logging.getLogger(__name__).exception(f"Failed to initialize AgentRegistry: {e}")
        except Exception:
            pass
    # Register monitoring metrics in a guarded way
        from twisterlab.monitoring_utils import register_with_app

        register_with_app(app)
    except Exception:
        pass
    # Integrate Prometheus Instrumentator in a guarded manner
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        if not getattr(app.state, "_instrumentator_attached", False):
            instr = Instrumentator()
            instr.instrument(app)
            app.state._instrumentator_attached = True
    except Exception:
        pass
    # If instrumentator is not available, fall back to exposing /metrics using prometheus_client.
    try:
        if FastAPIInstrumentor is not None:
            try:
                FastAPIInstrumentor.instrument_app(app)
            except Exception:
                pass

        from fastapi import Response as FastAPIResponse
        from prometheus_client import CONTENT_TYPE_LATEST  # type: ignore
        from prometheus_client import generate_latest

        if not any(
            getattr(route, "path", None) == "/metrics" for route in app.router.routes
        ):

            def _metrics_view():
                payload = generate_latest()
                return FastAPIResponse(content=payload, media_type=CONTENT_TYPE_LATEST)

            app.add_api_route("/metrics", _metrics_view, methods=["GET"])
    except Exception:
        pass
    # yield control back to FastAPI for runtime
    yield


# OpenAPI metadata for documentation
OPENAPI_TAGS = [
    {
        "name": "system",
        "description": "System health, metrics and configuration endpoints",
    },
    {
        "name": "agents",
        "description": "Agent management: create, list, update, and delete agents",
    },
    {
        "name": "mcp",
        "description": "Model Context Protocol (MCP) server integration",
    },
    {
        "name": "browser",
        "description": "Browser automation and screenshot capabilities",
    },
]

app = FastAPI(
    title="TwisterLab API",
    description="""
## TwisterLab - Multi-Agent Orchestration Platform

TwisterLab provides a unified API for managing and orchestrating AI agents.

### Features
- **Agent Management**: Register, monitor, and control multiple AI agents
- **MCP Integration**: Model Context Protocol server for IDE integration
- **Browser Automation**: Web scraping and screenshot capabilities
- **System Monitoring**: Health checks, metrics, and observability

### Authentication
Currently supports Bearer token authentication. OAuth2/OIDC coming in future versions.

### Rate Limiting
Rate limiting is enforced at {RATE_LIMIT_PER_MINUTE} requests per minute per IP (configurable via environment).

### CORS
Cross-origin requests are restricted to configured origins only.
    """,
    version="3.2.0",
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "TwisterLab Team",
        "url": "https://github.com/youneselfakir0/Twisterlab",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)


# Security configuration via environment variables
import os

# CORS Origins - comma-separated list, defaults to common development origins
# In production, set ALLOWED_ORIGINS=https://your-domain.com
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://localhost:8080,http://192.168.0.30:30091,http://192.168.0.30:30001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Rate limiting middleware
# Rate limiting middleware
import logging
logger = logging.getLogger(__name__)

from twisterlab.agents.api.security import RateLimitMiddleware
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT)
logger.info(f"✅ Security Middleware ENABLED with limit {RATE_LIMIT} req/min")

app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["mcp"])
app.include_router(routes_mcp_real.router, prefix="/api/v1/mcp/tools", tags=["mcp-tools"])
app.include_router(browser.router, prefix="/api/v1/browser", tags=["browser"])


@app.get("/")
async def root():
    return {"message": "Welcome to TwisterLab API"}


# Mount the simple UI (if present). Support both the package-relative path (src/twisterlab/ui/browser)
# and a more generic src/ui/browser path used in other environments.
pkg_ui = Path(__file__).resolve().parents[1] / "ui" / "browser"
generic_ui = Path(__file__).resolve().parents[2] / "ui" / "browser"
STATIC_UI = pkg_ui if pkg_ui.exists() else generic_ui
if STATIC_UI.exists():
    app.mount("/ui", StaticFiles(directory=str(STATIC_UI), html=True), name="ui")


# Ensure /metrics exists even if optional prometheus instrumentator is not installed.
# This is a lightweight runtime handler that attempts to use prometheus_client if available
# but otherwise returns a simple text body. Adding the route at module import time makes it
# available during TestClient initialization and in the container runtime prior to startup.
def _metrics_view():
    try:
        from prometheus_client import CONTENT_TYPE_LATEST  # type: ignore
        from prometheus_client import generate_latest

        payload = generate_latest()
        return FastAPIResponse(content=payload, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        # Fallback minimal text for tests/CI when prometheus_client isn't present
        return FastAPIResponse(
            content=b"# metrics unavailable\n", media_type="text/plain"
        )


if not any(getattr(route, "path", None) == "/metrics" for route in app.router.routes):
    app.add_api_route("/metrics", _metrics_view, methods=["GET"])
