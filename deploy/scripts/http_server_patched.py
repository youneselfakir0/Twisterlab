"""
MCP HTTP Server Wrapper

Exposes the Unified MCP Server via HTTP for K8s deployment.
Provides health checks and HTTP-based MCP communication.
"""

import logging
import os
import time
import asyncio
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.middleware.cors import CORSMiddleware
import httpx
from starlette.responses import StreamingResponse

from twisterlab.agents.mcp.server import UnifiedMCPServer
from twisterlab.monitoring.metrics import register_with_app

# Cache for health check to avoid slow blocking calls
health_cache = {"data": None, "expiry": 0}
CACHE_TTL = 5  # seconds

# OpenClaw config
OPENCLAW_CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")

async def _check_openclaw_health() -> dict:
    """Probe OpenClaw gateway with token. Returns {status, port, version}."""
    try:
        token = None
        if os.path.exists(OPENCLAW_CONFIG_PATH):
            with open(OPENCLAW_CONFIG_PATH) as f:
                cfg = json.load(f)
            token = cfg.get("gateway", {}).get("auth", {}).get("token")
            port = cfg.get("gateway", {}).get("port", 18789)
        else:
            port = 18789

        url = f"http://localhost:{port}/"
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        params = {"token": token} if token else {}

        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url, params=params, headers=headers)
            if r.status_code in (200, 101, 302):
                return {"status": "up", "port": port}
            else:
                return {"status": "down", "port": port, "http_code": r.status_code}
    except Exception as e:
        return {"status": "down", "port": 18789, "error": str(e)[:80]}

logging.basicConfig(
    level=getattr(logging, os.getenv("MCP_LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TwisterLab Unified MCP Server",
    description="HTTP wrapper for the MCP server",
    version="2.0.0",
)

# Add CORS for Dashboard - MUST BE BEFORE ROUTES
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register Prometheus Metrics Middleware
register_with_app(app)

# Global state for Live Maestro tracking
maestro_state = {
    "active_task": None,
    "last_result": None,
    "history": [],
    "active_steps": []
}

def update_maestro_progress(step_data):
    """Callback for Maestro to report progress."""
    global maestro_state
    maestro_state["active_steps"].append(step_data)
    logger.info(f"Maestro Progress: {step_data.get('agent')} -> {step_data.get('status')}")

# Global MCP server instance
mcp_server: UnifiedMCPServer = None

@app.on_event("startup")
async def startup():
    global mcp_server
    mcp_server = UnifiedMCPServer()
    # Inject callback for live reporting
    if hasattr(mcp_server, '_agent_registry'):
        maestro = mcp_server._agent_registry.get_agent("maestro")
        if maestro:
            maestro.status_callback = update_maestro_progress
            logger.info("Maestro live progress reporting enabled")
    logger.info(f"MCP Server started with {len(mcp_server._tool_router.list_tools())} tools")

# API Router for Compatibility
api_router = APIRouter(prefix="/api")

@api_router.get("/health")
async def health():
    """Health check endpoint for K8s."""
    return {
        "status": "healthy",
        "server": mcp_server.name if mcp_server else "not initialized",
        "version": mcp_server.version if mcp_server else "unknown",
        "tools": len(mcp_server._tool_router.list_tools()) if mcp_server else 0,
    }

@api_router.get("/")
async def api_root():
    """Root endpoint with server info."""
    return mcp_server.get_server_info() if mcp_server else {"error": "not initialized"}

@api_router.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")
    return {"tools": mcp_server._tool_router.list_tools()}

@api_router.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """Execute an MCP tool via HTTP."""
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")

    # Check cache for monitoring_health_check
    if tool_name == "monitoring_health_check":
        now = time.time()
        if health_cache["data"] and now < health_cache["expiry"]:
            return health_cache["data"]

    try:
        body = await request.json()
    except Exception:
        body = {}

    arguments = body.get("arguments", body)

    result = await mcp_server._tool_router.execute_tool(tool_name, arguments)

    # Normalize statuses for the dashboard
    if tool_name == "monitoring_health_check" and not result.get("isError"):
        try:
            if result.get("content") and len(result["content"]) > 0:
                data = json.loads(result["content"][0]["text"])
                # Handle nested structure: services -> system -> metadata -> services
                target_services = None
                if "services" in data and "system" in data["services"]:
                    target_services = data["services"]["system"].get("metadata", {}).get("services")
                elif "services" in data:
                    target_services = data["services"]

                if target_services is None:
                    target_services = {}
                    data["services"] = target_services

                # Dashboard is obviously UP if we're here
                target_services["api-bridge"] = {"status": "up", "port": 8000}

                # Probe OpenClaw with auth token
                try:
                    openclaw_status = await _check_openclaw_health()
                    target_services["openclaw"] = openclaw_status
                except Exception as oc_err:
                    target_services["openclaw"] = {"status": "down", "error": str(oc_err)[:80]}

                # Normalize all statuses
                VALID_UP = {"up", "connected", "running", "healthy", "ok", "online"}
                for svc in list(target_services.keys()):
                    info = target_services[svc]
                    if isinstance(info, dict):
                        s = str(info.get("status", "off")).lower()
                        info["status"] = "up" if s in VALID_UP else "down"

                result["content"][0]["text"] = json.dumps(data)
        except Exception as e:
            logger.error(f"Status normalization failed: {e}")

    # Update cache if it's the health check
    if tool_name == "monitoring_health_check":
        health_cache["data"] = result
        health_cache["expiry"] = time.time() + CACHE_TTL

    if result.get("isError"):
        raise HTTPException(400, result.get("content", [{"text": "Unknown error"}])[0].get("text"))

    return result

@app.get("/")
async def serve_index():
    """Serve the dashboard UI."""
    return FileResponse("index.html")

@app.get("/index.html")
async def serve_index_html():
    return FileResponse("index.html")

@app.get("/index.css")
async def serve_css():
    return FileResponse("index.css")

app.include_router(api_router)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    JSON-RPC endpoint for MCP protocol.

    Allows MCP clients to communicate via HTTP instead of stdio.
    """
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")

    try:
        rpc_request = await request.json()
        response = await mcp_server.handle_request(rpc_request)
        return response or {"jsonrpc": "2.0", "result": {}}
    except Exception as e:
        logger.exception("MCP request failed")
        return {
            "jsonrpc": "2.0",
            "id": 0,
            "error": {"code": -32603, "message": str(e)}
        }


@app.get("/api/agents")
async def list_agents():
    """List all registered agents."""
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")
    return {
        "agents": mcp_server._agent_registry.list_all()
    }


@app.get("/api/stats")
async def get_stats():
    """Get router statistics."""
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")
    return mcp_server._tool_router.get_stats()


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# --- N8N REVERSE PROXY (to bypass X-Frame-Options) ---

N8N_URL = "http://192.168.0.30:5678"

@app.api_route("/api/proxy/n8n/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_n8n(path: str, request: Request):
    return await _do_proxy(N8N_URL, path, request)

# Proxy for n8n assets located at /assets/
@app.api_route("/assets/{path:path}", methods=["GET"])
async def proxy_n8n_assets(path: str, request: Request):
    return await _do_proxy(N8N_URL, f"assets/{path}", request)

# Proxy for n8n API calls located at /rest/
@app.api_route("/rest/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_n8n_rest(path: str, request: Request):
    return await _do_proxy(N8N_URL, f"rest/{path}", request)

@app.api_route("/types/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_n8n_types(path: str, request: Request):
    return await _do_proxy(N8N_URL, f"types/{path}", request)

@app.api_route("/healthz", methods=["GET"])
async def proxy_n8n_health(request: Request):
    return await _do_proxy(N8N_URL, "healthz", request)

# Proxy for n8n nodes details
@app.api_route("/nodes/{path:path}", methods=["GET"])
async def proxy_n8n_nodes(path: str, request: Request):
    return await _do_proxy(N8N_URL, f"nodes/{path}", request)

# Shortcut /n8n/ route for iframe convenience
@app.get("/n8n/")
async def proxy_n8n_root(request: Request):
    return await _do_proxy(N8N_URL, "", request)

@app.api_route("/n8n/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_n8n_shortcut(path: str, request: Request):
    return await _do_proxy(N8N_URL, path, request)

async def _do_proxy(base_url: str, path: str, request: Request):
    url = f"{base_url}/{path}"
    query_params = str(request.query_params)
    if query_params:
        url += f"?{query_params}"
    
    # We use a dedicated client to manage timeouts better for long-lived streams
    async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
        headers = dict(request.headers)
        headers.pop("host", None)
        headers["accept-encoding"] = "identity" # Ensure no compression for easier manipulation
        
        try:
            req = client.build_request(
                method=request.method,
                url=url,
                headers=headers,
                content=await request.body()
            )
            res = await client.send(req, stream=True)
            
            # Handle Redirects BEFORE streaming
            if res.status_code in (301, 302, 303, 307, 308):
                location = res.headers.get("location", "")
                if location.startswith("/"):
                    # Prefix relative redirects with proxy path
                    new_location = f"/api/proxy/n8n{location}"
                    return RedirectResponse(new_location, status_code=res.status_code)
                return RedirectResponse(location, status_code=res.status_code)

            response_headers = dict(res.headers)
            # Remove transfer/encoding headers that we will re-manage
            for h in ["content-encoding", "content-length", "transfer-encoding", "connection"]:
                response_headers.pop(h, None)
            
            # STRIP SECURITY HEADERS
            response_headers.pop("X-Frame-Options", None)
            response_headers.pop("Content-Security-Policy", None)
            response_headers.pop("content-security-policy", None)
            response_headers["Access-Control-Allow-Origin"] = "*"
            
            content_type = response_headers.get("content-type", "").lower()
            
            if "text/html" in content_type:
                # For HTML, we MUST read and modify the <base> tag
                # We use a 30s timeout here to avoid hanging on slow HTML responses
                raw_content = await res.aread()
                body = raw_content.decode("utf-8", errors="ignore")
                base_tag = '<base href="/api/proxy/n8n/">'
                if "<head>" in body:
                    body = body.replace("<head>", f"<head>{base_tag}")
                else:
                    body = f"{base_tag}{body}"
                return Response(content=body.encode("utf-8"), status_code=res.status_code, headers=response_headers, media_type="text/html")
            
            # For everything else (JS, CSS, SSE), stream it!
            return StreamingResponse(
                res.aiter_raw(),
                status_code=res.status_code,
                headers=response_headers,
                media_type=content_type
            )
        except Exception as e:
            logger.error(f"Proxy critical error for {url}: {e}")
            return JSONResponse({"error": "Gateway Timeout", "details": str(e)}, status_code=504)

# --- NEW MAESTRO HUB API ---

@app.get("/api/maestro/status")
async def get_maestro_status():
    """Get the current orchestration state."""
    return maestro_state

@app.post("/api/maestro/dispatch")
async def dispatch_maestro_task(request: Request):
    """Trigger a new Maestro orchestration task from the dashboard."""
    body = await request.json()
    task = body.get("task")
    if not task:
        raise HTTPException(400, "Missing task description")
    
    global maestro_state
    maestro_state["active_task"] = task
    maestro_state["active_steps"] = []
    
    # Run orchestration in the background to not block the UI
    import asyncio
    async def run_task():
        try:
            result = await mcp_server._tool_router.execute_tool("maestro_orchestrate", {"task": task})
            maestro_state["last_result"] = result
            maestro_state["history"].append({"task": task, "status": "completed", "time": datetime.now().isoformat()})
        except Exception as e:
            maestro_state["last_result"] = {"error": str(e)}
            logger.error(f"Maestro dispatch failed: {e}")
        finally:
            maestro_state["active_task"] = None

    asyncio.create_task(run_task())
    return {"status": "dispatched", "task": task}

# --- STATIC CONTENT & DASHBOARD ---

WORKSPACE_DIR = r"c:\Users\Administrator\Documents\twisterlab"

app.mount("/dashboard-static", StaticFiles(directory=WORKSPACE_DIR), name="dashboard-static")

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(WORKSPACE_DIR, "index.html"))

# Fallback for /static/ - check local first, then proxy to n8n
@app.get("/static/{path:path}")
async def proxy_n8n_static_fallback(path: str, request: Request):
    local_path = os.path.join(WORKSPACE_DIR, "static", path)
    if os.path.exists(local_path):
        return FileResponse(local_path)
    return await _do_proxy(N8N_URL, f"static/{path}", request)

from datetime import datetime


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
