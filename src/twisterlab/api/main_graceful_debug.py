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

# This file is a debug/graceful variant of main.py
app = FastAPI(title="TwisterLab Debug API")

app.include_router(routes_mcp_real.router, prefix="/api/v1/mcp", tags=["mcp"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(browser.router, prefix="/api/v1/browser", tags=["browser"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "graceful-debug"}
