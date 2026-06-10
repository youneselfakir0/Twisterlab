import sys
import json
from pathlib import Path

# Add /app to sys.path to ensure twisterlab package is found
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Response as FastAPIResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from starlette.responses import RedirectResponse
import httpx
from fastapi import Request

# Optional instrumentation (OpenTelemetry) - import lazily and gracefully
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    FastAPIInstrumentor = None

from .routes import agents, browser, mcp, system, mcp_sse, tools
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
    version="3.5.0",
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
import os  # noqa: E402

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
import logging  # noqa: E402
logger = logging.getLogger(__name__)

from twisterlab.agents.api.security import RateLimitMiddleware  # noqa: E402
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT)
logger.info(f"✅ Security Middleware ENABLED with limit {RATE_LIMIT} req/min")

app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["mcp"])
app.include_router(mcp_sse.router, prefix="/api/v1/mcp", tags=["mcp-sse"])
app.include_router(routes_mcp_real.router, prefix="/api/v1/mcp/tools", tags=["mcp-tools"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(browser.router, prefix="/api/v1/browser", tags=["browser"])

# --- DASHBOARD PUBLIC ENDPOINTS (No Auth Needed) ---
async def _get_telemetry_snapshot():
    import time
    t0 = time.time()
    try:
        cpu, mem_pct, mem_used_gb, mem_total_gb, disk_pct, disk_used_gb, disk_total_gb = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            mem_pct = mem.percent
            mem_used_gb = round(mem.used / (1024**3), 1)
            mem_total_gb = round(mem.total / (1024**3), 1)
            disk_pct = disk.percent
            disk_used_gb = round(disk.used / (1024**3), 1)
            disk_total_gb = round(disk.total / (1024**3), 1)
        except (ImportError, Exception):
            import re
            try:
                def read_cpu():
                    with open('/proc/stat') as f:
                        line = f.readline()
                    vals = list(map(int, line.split()[1:8]))
                    return vals[3], sum(vals)
                i1, t1 = read_cpu()
                time.sleep(0.1)
                i2, t2 = read_cpu()
                dt = t2 - t1
                cpu = round((1 - (i2 - i1) / dt) * 100, 1) if dt > 0 else 0.0
            except: cpu = 0.0
            try:
                meminfo = {}
                with open('/proc/meminfo') as f:
                    for line in f:
                        k, v = line.split(':')  
                        meminfo[k.strip()] = int(v.split()[0])
                total_kb = meminfo.get('MemTotal', 1)
                avail_kb = meminfo.get('MemAvailable', total_kb)
                used_kb = total_kb - avail_kb
                mem_pct = round(used_kb / total_kb * 100, 1)
                mem_used_gb = round(used_kb / (1024**2), 1)
                mem_total_gb = round(total_kb / (1024**2), 1)
            except: pass
            try:
                import os
                stat = os.statvfs('/')
                total_b = stat.f_frsize * stat.f_blocks
                avail_b = stat.f_frsize * stat.f_bavail
                used_b = total_b - avail_b
                disk_pct = round(used_b / total_b * 100, 1) if total_b > 0 else 0.0
                disk_used_gb = round(used_b / (1024**3), 1)
                disk_total_gb = round(total_b / (1024**3), 1)
            except: pass
        
        return {
            "agents": [],
            "services": {
                "system": {
                    "cpu_percent": round(cpu, 1),
                    "memory_percent": round(mem_pct, 1),
                    "memory_total_gb": mem_total_gb,
                    "memory_used_gb": mem_used_gb,
                    "disk_percent": round(disk_pct, 1),
                    "disk_total_gb": disk_total_gb,
                    "disk_used_gb": disk_used_gb,
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                }
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/dashboard/telemetry")
@app.get("/api/dashboard/telemetry")
async def public_monitoring_health_check():
    data = await _get_telemetry_snapshot()
    return {"content": [{"text": json.dumps(data)}], "isError": False}



@app.post("/api/dashboard/history")
@app.get("/api/dashboard/history")
async def public_archive_history():
    """Return real mission archive from /app/archives if available."""
    import os, json as _json
    archive_dir = "/app/archives/missions"
    try:
        os.makedirs(archive_dir, exist_ok=True)
        files = sorted(os.listdir(archive_dir), reverse=True)[:15] if os.path.exists(archive_dir) else []
        items = []
        for f in files:
            fp = os.path.join(archive_dir, f)
            try:
                with open(fp) as fh:
                    d = _json.load(fh)
                items.append({"id": f.replace('.json',''), "file": f, "data": d,
                               "timestamp": d.get("timestamp", ""),
                               "task": d.get("task", d.get("mission_id", f))})
            except Exception:
                items.append({"id": f.replace('.json',''), "file": f})
        return {
            "content": [{"text": json.dumps({"status": "success", "data": items, "count": len(items)})}],
            "isError": False
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/dashboard/archive")
async def archive_mission(request: Request):
    """Save a mission to /app/archives/missions — no auth required."""
    import os, json as _json
    from datetime import datetime, timezone
    try:
        raw_body = await request.body()
        body = _json.loads(raw_body.decode("utf-8", errors="replace"))
        mission_id = body.get("mission_id", f"M-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
        data = body.get("data", body)
        if isinstance(data, str):
            data = {"raw": data}
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        archive_dir = "/app/archives/missions"
        os.makedirs(archive_dir, exist_ok=True)
        filename = f"mission_{mission_id}_{datetime.now(timezone.utc).strftime('%H%M%S')}.json"
        filepath = os.path.join(archive_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            _json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Mission {mission_id} archived to {filepath}")
        return {
            "content": [{"text": json.dumps({"status": "archived", "mission_id": mission_id, "file": filename})}],
            "isError": False
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/dashboard/history/delete")
async def delete_archive_mission(request: Request):
    """Delete a mission log from /app/archives/missions."""
    import os, json as _json
    try:
        raw_body = await request.body()
        body = _json.loads(raw_body.decode("utf-8", errors="replace"))
        mission_id = body.get("mission_id")
        if not mission_id:
            return {"status": "error", "message": "mission_id required"}
        archive_dir = "/app/archives/missions"
        if not os.path.exists(archive_dir):
            return {"status": "error", "message": "No archives found"}
        files = os.listdir(archive_dir)
        deleted = False
        for f in files:
            if mission_id in f and f.endswith(".json"):
                os.remove(os.path.join(archive_dir, f))
                deleted = True
        if deleted:
            return {"content": [{"text": json.dumps({"status": "deleted", "mission_id": mission_id})}], "isError": False}
        return {"status": "error", "message": f"Mission {mission_id} not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/dashboard/agents")
async def dashboard_agents():
    """Return the real live agent list from the AgentRegistry."""
    try:
        from twisterlab.agents.registry import AgentRegistry
        registry = AgentRegistry()
        agents_out = []
        for agent in registry._agent_list:
            caps = []
            try:
                caps = [c.name for c in agent.get_capabilities()]
            except Exception:
                pass
            agents_out.append({
                "name": agent.name,
                "class": type(agent).__name__,
                "description": getattr(agent, 'description', ''),
                "capabilities": caps,
                "status": "online"
            })
        return {"agents": agents_out, "count": len(agents_out)}
    except Exception as e:
        # Fallback: return the static list of known agents
        return {
            "agents": [
                {"name": "maestro", "class": "RealMaestroAgent", "status": "online", "tag": "orchestrator"},
                {"name": "monitoring", "class": "RealMonitoringAgent", "status": "online", "tag": "infra"},
                {"name": "real-desktop-commander", "class": "RealDesktopCommanderAgent", "status": "online", "tag": "system"},
                {"name": "browser", "class": "RealBrowserAgent", "status": "online", "tag": "web"},
                {"name": "real-classifier", "class": "RealClassifierAgent", "status": "online", "tag": "nlp"},
                {"name": "real-resolver", "class": "RealResolverAgent", "status": "online", "tag": "support"},
                {"name": "sentiment-analyzer", "class": "SentimentAnalyzerAgent", "status": "online", "tag": "nlp"},
                {"name": "code-review", "class": "RealCodeReviewAgent", "status": "online", "tag": "dev"},
                {"name": "cache", "class": "CacheAgent", "status": "online", "tag": "redis"},
                {"name": "database", "class": "DatabaseAgent", "status": "online", "tag": "postgres"},
                {"name": "real-backup", "class": "RealBackupAgent", "status": "online", "tag": "persistence"},
                {"name": "real-sync", "class": "RealSyncAgent", "status": "online", "tag": "sync"},
            ],
            "count": 12,
            "error": str(e)
        }


@app.get("/api/dashboard/services")
async def dashboard_services():
    """Probe connectivity of key TwisterLab services."""
    import asyncio
    probes = [
        {"name": "API Bridge",  "url": "http://localhost:8000/api/v1/system/health", "port": 30000, "label": "api"},
        {"name": "n8n Engine",  "url": f"{N8N_URL}/healthz",                          "port": 5678,  "label": "n8n"},
        {"name": "Grafana",     "url": "http://192.168.0.30:30091/api/health",         "port": 30091, "label": "grafana"},
        {"name": "Prometheus",  "url": "http://192.168.0.30:30090/-/ready",           "port": 30090, "label": "prometheus"},
    ]
    results = []
    async with httpx.AsyncClient(timeout=2.0) as client:
        for svc in probes:
            try:
                r = await client.get(svc["url"])
                status = "up" if r.status_code < 500 else "degraded"
            except Exception:
                status = "down"
            results.append({"name": svc["name"], "port": svc["port"],
                            "label": svc["label"], "status": status})
    return {"services": results}


@app.get("/api/dashboard/n8n")
async def dashboard_n8n():
    """Fetch n8n workflows and recent executions via REST API."""
    api_key = os.getenv("N8N_API_KEY", "")
    headers = {}
    if api_key:
        headers["X-N8N-API-KEY"] = api_key

    try:
        async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
            wf_r = await client.get(f"{N8N_URL}/rest/workflows")
            ex_r = await client.get(f"{N8N_URL}/rest/executions?limit=15")

            workflows = []
            executions = []
            auth_required = False

            if wf_r.status_code == 200:
                d = wf_r.json()
                workflows = d.get("data", d) if isinstance(d, dict) else d
            elif wf_r.status_code == 401:
                auth_required = True

            if ex_r.status_code == 200:
                d = ex_r.json()
                executions = d.get("results", d.get("data", []))

            return {
                "status": "online",
                "auth_required": auth_required,
                "api_key_configured": bool(api_key),
                "workflows": workflows,
                "executions": executions,
            }
    except Exception as e:
        return {"status": "offline", "error": str(e), "workflows": [], "executions": []}

# Mock missing static assets
@app.get("/static/{path:path}")
async def mock_static_assets(path: str):
    if path in ["base-path.js", "posthog.init.js"]:
        return FastAPIResponse(content="console.log('Mocked asset: " + path + "')", media_type="application/javascript")
    if path == "prefers-color-scheme.css":
        return FastAPIResponse(content="/* Mocked */", media_type="text/css")
    return FastAPIResponse(status_code=404)

app.include_router(tools.router, prefix="/api/tools", tags=["tools"])


# --- N8N REVERSE PROXY (to bypass X-Frame-Options) ---

N8N_URL = os.getenv("N8N_URL", "http://192.168.0.30:5678")

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
                elif "localhost" in location or "127.0.0.1" in location:
                    # Rewrite localhost redirects to use the proxy path
                    from urllib.parse import urlparse
                    parsed = urlparse(location)
                    new_location = f"/api/proxy/n8n{parsed.path}"
                    if parsed.query:
                        new_location += f"?{parsed.query}"
                    return RedirectResponse(new_location, status_code=res.status_code)
                return RedirectResponse(location, status_code=res.status_code)

            response_headers = dict(res.headers)
            # Remove transfer/encoding headers that we will re-manage
            for h in ["content-encoding", "content-length", "transfer-encoding", "connection"]:
                response_headers.pop(h, None)
            
            # AGGRESSIVELY STRIP SECURITY HEADERS to allow framing
            # Note: headers are case-insensitive in dict keys if it's a CaseInsensitiveDict, 
            # but here it's a standard dict from res.headers, so we use a lowercase loop.
            headers_to_remove = [
                "x-frame-options", "content-security-policy", "x-content-type-options",
                "x-xss-protection", "strict-transport-security", "permissions-policy"
            ]
            final_headers = {}
            for k, v in response_headers.items():
                if k.lower() not in headers_to_remove:
                    final_headers[k] = v
            
            # AGGRESSIVELY ALLOW FRAMING
            final_headers["X-Frame-Options"] = "ALLOWALL"
            final_headers["Content-Security-Policy"] = "frame-ancestors 'self' *"
            final_headers["Access-Control-Allow-Origin"] = "*"
            final_headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            final_headers["Access-Control-Allow-Headers"] = "*"
            
            content_type = final_headers.get("content-type", "").lower()
            
            if "text/html" in content_type or "javascript" in content_type:
                # For HTML and JS, we MUST read and modify the content to fix internal links/port references
                raw_content = await res.aread()
                body = raw_content.decode("utf-8", errors="ignore")
                
                # REWRITE LOCALHOST REFERENCES that cause CSP/frame errors
                # (e.g., n8n sometimes points to its internal pod port)
                import re
                body = re.sub(r'https?://localhost:\d+/?', '/api/proxy/n8n/', body)
                body = re.sub(r'https?://127\.0\.0\.1:\d+/?', '/api/proxy/n8n/', body)
                
                if "text/html" in content_type:
                    base_tag = '<base href="/api/proxy/n8n/">'
                    if "<head>" in body:
                        body = body.replace("<head>", f"<head>{base_tag}")
                    else:
                        body = f"{base_tag}{body}"
                
                return FastAPIResponse(content=body.encode("utf-8"), status_code=res.status_code, headers=response_headers, media_type=content_type)
            
            # For everything else (JS, CSS, SSE), stream it!
            return StreamingResponse(
                res.aiter_raw(),
                status_code=res.status_code,
                headers=response_headers,
                media_type=content_type
            )
        except Exception as e:
            logger.error(f"Proxy critical error for {url}: {e}")
            return FastAPIResponse(content=json.dumps({"error": "Gateway Timeout", "details": str(e)}), status_code=504, media_type="application/json")

@app.api_route("/api/proxy/n8n/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_n8n(path: str, request: Request):
    return await _do_proxy(N8N_URL, path, request)

@app.api_route("/assets/{path:path}", methods=["GET"])
async def proxy_n8n_assets(path: str, request: Request):
    return await _do_proxy(N8N_URL, f"assets/{path}", request)

@app.api_route("/rest/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_n8n_rest(path: str, request: Request):
    return await _do_proxy(N8N_URL, f"rest/{path}", request)

@app.get("/n8n/")
async def proxy_n8n_root(request: Request):
    return await _do_proxy(N8N_URL, "", request)


@app.get("/")
async def root():
    root_path = Path(__file__).resolve().parents[3]
    index_path = root_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to TwisterLab API - Dashboard (index.html) not found"}

@app.get("/index.html")
async def serve_index():
    return await root()

@app.get("/index.css")
async def serve_css():
    root_path = Path(__file__).resolve().parents[3]
    css_path = root_path / "index.css"
    if css_path.exists():
        return FileResponse(css_path)
    return FastAPIResponse(status_code=404)


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


# --- CORTEX AI ENHANCED (Context + Memory) ---

async def _get_system_context():
    """Build a real-time system snapshot for the LLM."""
    tel = await _get_telemetry_snapshot()
    stats = tel.get("services", {}).get("system", {}) if "error" not in tel else {}
    
    agent_names = []
    try:
        from twisterlab.agents.registry import AgentRegistry
        registry = AgentRegistry()
        agent_names = [a.name for a in registry._agent_list]
    except: pass
    
    ctx = "[INFRASTRUCTURE LIVE]\n"
    if stats:
        ctx += f"- CPU: {stats.get('cpu_percent', 0)}% | RAM: {stats.get('memory_percent', 0)}% ({stats.get('memory_used_gb', 0)}/{stats.get('memory_total_gb', 0)}GB)\n"
        ctx += f"- Disque: {stats.get('disk_percent', 0)}% utilisé\n"
    ctx += f"- Agents actifs ({len(agent_names)}): {', '.join(agent_names)}\n"
    ctx += "- Server: EdgeServer-OPS (192.168.0.30) | Cluster: K3s\n"
    return ctx

OLLAMA_URLS = [
    os.getenv("OLLAMA_BASE_URL", "http://192.168.0.30:11434"),
    "http://192.168.0.30:11434",
    "http://localhost:11434",
]
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

CORTEX_SYSTEM = """Tu es Cortex IA, l'assistant expert du TwisterLab Mission Control v3.7.2.

CONSIGNES DE QUALITÉ :
- Utilise UNIQUEMENT les métriques de [INFRASTRUCTURE LIVE] (CPU, RAM, Disque).
- NE PAS inventer de pourcentages ou d'états non listés.
- Sois concis, technique et proactif.
- Diagnostic : Recommander `k3s status edge-server` ou l'agent Monitoring.
- Orchestration : Utiliser `Maestro` pour piloter les agents ou archiver les missions.
- Automation : Utiliser `n8n` pour les missions complexes.
- Emojis système : ⚡🔧🎯📊🤖."""


async def _call_ollama(prompt: str, model: str = None, history: list = None) -> str:
    """Try each Ollama URL until one works."""
    target_model = model or OLLAMA_MODEL
    
    # Format history
    hist_str = ""
    if history:
        for m in history[-8:]: # Last 8 messages
            role = "Utilisateur" if m.get("role") == "human" else "Cortex"
            hist_str += f"{role}: {m.get('text', '')}\n"

    final_prompt = f"{CORTEX_SYSTEM}\n\n{hist_str}Utilisateur: {prompt}\nCortex:"
    
    payload = {
        "model": target_model,
        "prompt": final_prompt,
        "stream": False,
        "options": {"temperature": 0.4} # Lower temp for accuracy
    }
    
    seen = []
    for url in OLLAMA_URLS:
        if url in seen or not url: continue
        seen.append(url)
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                r = await client.post(f"{url}/api/generate", json=payload)
                if r.status_code == 200:
                    return r.json().get("response", "").strip()
        except: continue
    raise RuntimeError("Ollama unreachable")


@app.post("/api/dashboard/cortex")
async def cortex_chat(request: Request):
    try:
        raw = await request.body()
        body = json.loads(raw.decode("utf-8", errors="replace"))
        input_text = body.get("input") or body.get("prompt") or ""
        history = body.get("history", [])
        model = body.get("model")
        
        if not input_text:
            return {"content": [{"text": "⚠️ Aucun input."}], "isError": True}
        
        # Inject live context
        context = await _get_system_context()
        full_input = f"{context}\n\n{input_text}"
        
        text = await _call_ollama(full_input, model, history)
        return {"content": [{"text": text}], "isError": False}
    except Exception as e:
        return {"content": [{"text": f"❌ Erreur: {str(e)}"}], "isError": True}


@app.get("/api/dashboard/cortex/models")
async def cortex_models():
    for url in OLLAMA_URLS:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{url}/api/tags")
                if r.status_code == 200:
                    models = r.json().get("models", [])
                    return {"models": [m["name"] for m in models], "url": url, "default": OLLAMA_MODEL}
        except: continue
    return {"models": [], "error": "Ollama unreachable"}
