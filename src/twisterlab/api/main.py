import logging
import os
import sys
import time
import asyncio
import psutil
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# TwisterLab Imports
from twisterlab.agents.registry import get_agent_registry, AgentStatus
from twisterlab.config.unified_settings import settings
from twisterlab.monitoring_utils import get_metric_values

# Router Imports
from twisterlab.api.routes import system, agents, mcp, mcp_sse, tools, browser, learning, maestro
from twisterlab.api import routes_mcp_real as mcp_real

# Logging Configuration
if not settings.core.debug:
    from twisterlab.utils.logging import setup_production_logging
    setup_production_logging()
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
logger = logging.getLogger("twisterlab.api")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Client: {websocket.client}. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Silent cleanup of broken connections during broadcast
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

manager = ConnectionManager()

# --- LOG BUFFERING ---
class LogBufferHandler(logging.Handler):
    def __init__(self, capacity=50):
        super().__init__()
        self.buffer = []
        self.capacity = capacity

    def emit(self, record):
        log_entry = {
            "timestamp": time.strftime("%H:%M:%S", time.localtime(record.created)),
            "type": self._get_type(record),
            "text": record.getMessage()
        }
        self.buffer.append(log_entry)
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)

    def _get_type(self, record):
        if record.levelno >= logging.ERROR: return "error"
        if "Call:" in record.msg or "Tool" in record.msg: return "tool"
        if "Result:" in record.msg or "Return" in record.msg: return "result"
        return "info"

log_buffer = LogBufferHandler()
logging.getLogger().addHandler(log_buffer)
# ---------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 TwisterLab API starting...")
    
    # Validate critical environment
    from twisterlab.utils.validation import validate_environment
    validate_environment()
    
    # Initialize database tables
    try:
        from twisterlab.database.session import init_db
        await init_db()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        
    # Start background scheduler
    try:
        from twisterlab.services.learning import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {e}")
        
    registry = get_agent_registry()
    
    # Pre-initialize critical agents
    logger.info("Initializing Maestro agent...")
    await asyncio.to_thread(registry.get_agent, "maestro")
    logger.info("Maestro initialized.")
    
    yield
    # Shutdown
    logger.info("🛑 TwisterLab API shutting down...")

app = FastAPI(
    title="TwisterLab Mission Control API",
    version=settings.core.version,
    lifespan=lifespan
)

# CORS Middleware
# Note: For production, specify real origins. Using "*" for compatibility.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["mcp"])
app.include_router(mcp_sse.router, prefix="/api/v1/mcp", tags=["mcp-sse"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(browser.router, prefix="/api/v1/browser", tags=["browser"])
app.include_router(mcp_real.router, prefix="/api/v1/mcp/tools", tags=["mcp-real"])
app.include_router(learning.router, prefix="/api/v1/learning", tags=["learning"])
app.include_router(maestro.router, prefix="/api/v1/maestro", tags=["maestro"])

# --- ENDPOINTS STANDARDS (PROMETHEUS/K8S) ---
@app.get("/metrics")
async def root_metrics():
    return await system.metrics()

@app.get("/health")
async def root_health():
    return await system.health_check()
# --------------------------------------------

# WebSocket Telemetry Endpoint
@app.websocket("/ws/telemetry")
async def telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        from twisterlab.utils.validation import validate_environment
        while True:
            registry = get_agent_registry()
            status = registry.get_registry_status()
            
            # Health & Environment Validation
            is_valid = validate_environment()
            
            # Real-time System Stats
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent
            
            # Metrics from Prometheus Registry
            metrics = get_metric_values()
            
            payload = {
                "type": "TELEMETRY_UPDATE",
                "timestamp": time.time(),
                "cpu": cpu_usage,
                "ram": ram_usage,
                "agents": status["total"],
                "active_agents": status["initialized"],
                "status": "ONLINE" if status["initialized"] > 0 and is_valid else "DEGRADED",
                "config_ok": is_valid,
                "metrics": metrics,
                "logs": log_buffer.buffer # Add buffered logs
            }
            
            await websocket.send_json(payload)
            await asyncio.sleep(2) # Update every 2 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in telemetry WebSocket: {e}")
        manager.disconnect(websocket)

# Static UI Mounting (if exists)
ui_path = Path(__file__).resolve().parents[3] / "frontend" / "dist"
if ui_path.exists():
    app.mount("/", StaticFiles(directory=str(ui_path), html=True), name="ui")
    logger.info(f"Mounted Static UI from {ui_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
