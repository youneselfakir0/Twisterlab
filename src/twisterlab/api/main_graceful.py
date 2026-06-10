import uuid
import os
import re
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi import Response as FastAPIResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

# Optional instrumentation (OpenTelemetry)
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
except Exception:
    FastAPIInstrumentor = None

from . import routes_mcp_real
from .routes import agents, browser, mcp, mcp_sse, system, tools

# GRACEFUL MCPResponse
try:
    from .schemas.common import MCPResponse
except ImportError:
    try:
        from .routes_mcp_real import MCPResponse
    except ImportError:
        from pydantic import BaseModel, Field
        class MCPResponse(BaseModel):
            status: str
            data: dict = None
            error: str = None
            isError: bool = False

logger = logging.getLogger(__name__)
DEBUG = os.getenv("TWISTERLAB_DEBUG", "false").lower() == "true"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. DB Initialization
    import twisterlab.database.models.agent  # noqa: F401
    from twisterlab.database.session import Base, engine

    try:
        if hasattr(engine, "begin"):
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            bind_engine = getattr(engine, "sync_engine", engine)
            Base.metadata.create_all(bind=bind_engine)
    except Exception:
        logger.exception("Failed to initialize DB tables")

    # 2. Agent Registry Warm-up
    try:
        from twisterlab.agents.registry import AgentRegistry
        registry = AgentRegistry()
        logger.info(f"AgentRegistry ready. Count: {len(registry)}")
    except Exception:
        logger.exception("Failed to initialize registry")

    yield

OPENAPI_TAGS = [
    {"name": "system", "description": "System health"},
    {"name": "agents", "description": "Agent management"},
]

app = FastAPI(
    title="TwisterLab Core API",
    version="3.9.2",
    lifespan=lifespan,
)

# Security
from twisterlab.agents.api.security import RateLimitMiddleware
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "500"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT)

# Routes
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["mcp"])
app.include_router(mcp_sse.router, prefix="/api/v1/mcp", tags=["mcp-sse"])
app.include_router(routes_mcp_real.router, prefix="/api/v1/mcp/tools", tags=["mcp-tools"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(browser.router, prefix="/api/v1/browser", tags=["browser"])

# Fallback Telemetry
@app.get("/api/dashboard/telemetry")
@app.post("/api/dashboard/telemetry")
async def public_telemetry():
    return {"content": [{"text": json.dumps({"services":{"system":{"cpu_percent":0,"memory_percent":0}}})}]}

@app.get("/health")
async def health(): return {"status": "ok"}

# --- UI SERVING ---
def get_index_path():
    # Attempt multiple paths for resilience
    paths = [
        Path("/app/index.html"),
        Path(__file__).resolve().parents[3] / "index.html",
        Path("index.html")
    ]
    for p in paths:
        if p.exists(): return p
    return None

@app.get("/")
async def root():
    p = get_index_path()
    if p: return FileResponse(p)
    return {"message": "UI index.html not found"}

@app.get("/index.html")
async def serve_index():
    return await root()

@app.get("/index.css")
async def serve_css():
    p = Path("/app/index.css")
    if not p.exists():
        p = Path(__file__).resolve().parents[3] / "index.css"
    if p.exists(): return FileResponse(p)
    return FastAPIResponse(status_code=404)
