import logging
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI

# Add project root to Python path to allow importing agents package
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import routers from the new modular structure
from api.routes import agents, system  # noqa: E402

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create the main FastAPI app instance
app = FastAPI(
    title="TwisterLab Autonomous Agents API v2",
    description="API for the TwisterLab v2 'Living IT System' ecosystem.",
    version="2.0.0",
)

# Include the routers from the separate modules
app.include_router(system.router)
app.include_router(agents.router)
try:
    from api.routes import auth

    app.include_router(auth.router)
    logger.info("Auth routes (/auth/*) included in API main app")
except Exception:
    logger.warning("Auth routes could not be included (possibly missing dependencies)")

try:
    from api.auth_hybrid import router as auth_hybrid_router

    app.include_router(auth_hybrid_router, prefix="/auth")
    logger.info("Hybrid auth routes included (/auth/*)")
except Exception:
    logger.warning("Hybrid auth routes not included (missing optional deps)")
try:
    # Include MCP routes (real agents) so tests and external clients can call /v1/mcp/tools/*
    from agents.api.routes_mcp_real import router as mcp_real_router

    logger.info(f"MCP router imported successfully, routes: {len(mcp_real_router.routes)}")

    # Mount the real MCP routes under the REST API prefix so they are available
    # as '/v1/mcp/tools/<tool>' which is the conventional API expected by clients.
    app.include_router(mcp_real_router)  # MCP tools router (already has /v1/mcp/tools prefix)
    logger.info("MCP routes (/v1/mcp/tools) included in API main app")
except Exception as e:
    logger.warning(f"Could not include MCP routes: {e}")
    import traceback

    logger.warning(f"Traceback: {traceback.format_exc()}")

try:
    # Include REST wrapper for MCP (v1) for backward compatibility
    from api.endpoints.mcp_rest import router as mcp_rest_router

    app.include_router(mcp_rest_router)
    logger.info("MCP REST wrapper routes (/v1/mcp) included in API main app")
except Exception as e:
    logger.warning(f"Could not include MCP REST router: {e}")

logger.info("FastAPI application created and routers included.")
logger.info("System router loaded with endpoints: /health, /token, /metrics")
logger.info("Agents router loaded with endpoints: /api/v1/autonomous/agents/*")


@app.get("/")
async def root():
    return {"status": "ok", "message": "TwisterLab API v2"}


async def execute_monitoring_agent(payload: Dict[str, Any]):
    """Helper used by tests and integration to execute the MonitoringAgent.

    This is intentionally small and can be mocked by tests.
    """
    from agents.real.real_monitoring_agent import RealMonitoringAgent

    agent = RealMonitoringAgent()
    # Normalize payload shape
    if isinstance(payload, dict):
        context = payload
    else:
        context = {"operation": "check_health"}
    return await agent.execute(context)


# Main entry point for running the server directly
if __name__ == "__main__":
    import uvicorn

    try:
        logger.info("Starting TwisterLab API v2 server...")

        # The agent registry is automatically initialized on first import,
        # which happens when the routers are imported.

        uvicorn.run(app, host="0.0.0.0", port=8000)

    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        import traceback

        logger.error(traceback.format_exc())
        raise
