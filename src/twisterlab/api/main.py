import uuid
import os
import re
import json
import logging
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

# Optional instrumentation (OpenTelemetry) - import lazily and gracefully
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
except Exception:  # pragma: no cover
    FastAPIInstrumentor = None

from . import routes_mcp_real, routes_trading_ui, routes_trading_live
from .routes import agents, browser, mcp, mcp_sse, system, tools
from .schemas.common import MCPResponse

logger = logging.getLogger(__name__)
DEBUG = os.getenv("TWISTERLAB_DEBUG", "false").lower() == "true"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. DB Initialization
    import twisterlab.database.models.agent  # noqa: F401
    import twisterlab.database.models.trading # noqa: F401
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

    # 2. Agent Registry Warm-up (Optional & Env-Driven)
    try:
        from twisterlab.agents.registry import get_agent_registry
        registry = get_agent_registry()
        
        warm_agents_env = os.getenv("TWISTERLAB_WARM_AGENTS", "").strip()
        if warm_agents_env:
            warm_list = [name.strip() for name in warm_agents_env.split(",") if name.strip()]
            logger.info(f"Warming up priority agents: {warm_list}...")
            for name in warm_list:
                registry.get_agent(name)
        
        status = registry.get_registry_status()
        logger.info(f"AgentRegistry ready. Total: {status['total']}, Online: {status['initialized']}")
    except Exception:
        logger.exception("Failed to initialize registry warm-up")

    # 3. Metrics & Instrumentation
    try:
        from twisterlab.monitoring_utils import register_with_app
        register_with_app(app)
        
        from prometheus_fastapi_instrumentator import Instrumentator
        if not getattr(app.state, "_instrumentator_attached", False):
            Instrumentator().instrument(app).expose(app, endpoint="/metrics")
            app.state._instrumentator_attached = True
            
        if FastAPIInstrumentor is not None:
            FastAPIInstrumentor.instrument_app(app)
    except Exception:
        logger.warning("Monitoring/Metrics registration partially failed")

    # 4. Trading Services (Phase 7 & 11)
    from twisterlab.services.trading.stop_manager_service import StopManagerService
    from twisterlab.services.trading.execution_service import ExecutionGatewayService
    from twisterlab.services.trading.scanner_service import ScannerService
    from twisterlab.database.session import AsyncSessionLocal
    from twisterlab.config.settings import Settings
    
    settings = Settings()
    execution_gateway = ExecutionGatewayService(settings)
    stop_manager = StopManagerService(settings, execution_gateway)
    scanner = ScannerService(settings)
    
    # Store in app state for access if needed
    app.state.stop_manager = stop_manager
    app.state.scanner = scanner
    
    await stop_manager.start(AsyncSessionLocal)
    await scanner.start()
    logger.info("Phase 11: Multi-Strategy ScannerService started.")
    logger.info("Phase 7: StopManagerService integration COMPLETE.")

    yield
    
    # 5. Graceful Shutdown
    logger.info("Graceful shutdown initiated...")
    
    # Stop the Trading Services
    try:
        await scanner.stop()
        await stop_manager.stop()
        await execution_gateway.close()
    except Exception as e:
        logger.error(f"Failed to stop trading services: {e}")

    try:
        from twisterlab.agents.registry import get_agent_registry
        registry = get_agent_registry()
        # Potential cleanup per agent if implemented
        logger.info("Cleaning up agent resources...")
    except Exception as e:
        logger.error(f"Shutdown cleanup failed: {e}")


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
    title="TwisterLab Core API",
    description="Multi-Agent Orchestration Platform v3.8.2",
    version="3.8.2",
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
logger = logging.getLogger(__name__)

from twisterlab.agents.api.security import RateLimitMiddleware  # noqa: E402

RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT)
logger.info(f"[SECURITY] RateLimit Middleware ENABLED: {RATE_LIMIT} req/min")

# --- CORE ROUTES ---
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["mcp"])
app.include_router(mcp_sse.router, prefix="/api/v1/mcp", tags=["mcp-sse"])
app.include_router(
    routes_mcp_real.router, prefix="/api/v1/mcp/tools", tags=["mcp-tools"]
)
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(browser.router, prefix="/api/v1/browser", tags=["browser"])
app.include_router(
    routes_trading_ui.router,
    prefix="/api/v1/trader/dashboard",
    tags=["trader-dashboard"],
)
app.include_router(
    routes_trading_live.router,
    prefix="/api/v1/trader/live",
    tags=["trader-live"],
)

# --- DASHBOARD PUBLIC ENDPOINTS ---


async def _get_telemetry_snapshot():
    import time
    from twisterlab.agents.registry import get_agent_registry
    t0 = time.time()
    try:
        registry = get_agent_registry()
        reg_status = registry.get_registry_status()
        
        cpu, mem_pct, mem_used_gb, mem_total_gb, disk_pct = 0.0, 0.0, 0.0, 0.0, 0.0
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            mem_pct = mem.percent
            mem_used_gb = round(mem.used / (1024 ** 3), 2)
            mem_total_gb = round(mem.total / (1024 ** 3), 2)
            disk = psutil.disk_usage('/')
            disk_pct = disk.percent
        except (ImportError, Exception):
            pass

        return {
            "agents": {
                "total": reg_status["total"],
                "initialized": reg_status["initialized"],
                "status": reg_status["status_breakdown"]
            },
            "services": {
                "system": {
                    "cpu_percent": round(cpu, 1),
                    "memory_percent": round(mem_pct, 1),
                    "memory_used_gb": mem_used_gb,
                    "memory_total_gb": mem_total_gb,
                    "disk_percent": round(disk_pct, 1),
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                }
            },
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
    import os
    import json as _json

    archive_dir = "/app/archives/missions"
    try:
        os.makedirs(archive_dir, exist_ok=True)
        files = (
            sorted(os.listdir(archive_dir), reverse=True)[:15]
            if os.path.exists(archive_dir)
            else []
        )
        items = []
        for f in files:
            fp = os.path.join(archive_dir, f)
            try:
                with open(fp) as fh:
                    d = _json.load(fh)
                items.append(
                    {
                        "id": f.replace(".json", ""),
                        "file": f,
                        "data": d,
                        "timestamp": d.get("timestamp", ""),
                        "task": d.get("task", d.get("mission_id", f)),
                    }
                )
            except Exception:
                items.append({"id": f.replace(".json", ""), "file": f})
        return {
            "content": [
                {
                    "text": json.dumps(
                        {"status": "success", "data": items, "count": len(items)}
                    )
                }
            ],
            "isError": False,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/dashboard/archive")
async def archive_mission(request: Request):
    """Save a mission to /app/archives/missions ? no auth required."""
    import os
    import json as _json
    from datetime import datetime, timezone

    try:
        raw_body = await request.body()
        body = _json.loads(raw_body.decode("utf-8", errors="replace"))
        mission_id = body.get(
            "mission_id",
            f"M-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        )
        data = body.get("data", body)
        if isinstance(data, str):
            data = {"raw": data}
        
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        archive_dir = "/app/archives/missions"
        os.makedirs(archive_dir, exist_ok=True)
        filename = (
            f"mission_{mission_id}_{datetime.now(timezone.utc).strftime('%H%M%S')}.json"
        )
        filepath = os.path.join(archive_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            _json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Mission {mission_id} archived to {filepath}")
        return {
            "content": [
                {
                    "text": json.dumps(
                        {
                            "status": "archived",
                            "mission_id": mission_id,
                            "file": filename,
                        }
                    )
                }
            ],
            "isError": False,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/dashboard/agents")
async def dashboard_agents():
    """Return the real dynamic agent list from the AgentRegistry (Static-First)."""
    try:
        from twisterlab.agents.registry import get_agent_registry
        registry = get_agent_registry()
        agents_data = registry.list_agents()
        return {
            "agents": [
                {"id": k, **v} for k, v in agents_data.items()
            ],
            "count": len(agents_data)
        }
    except Exception as e:
        return {"agents": [], "count": 0, "error": str(e)}


@app.get("/api/dashboard/notion")
async def dashboard_notion():
    """Fetch Notion pages for dashboard display using RealNotionAgent."""
    from datetime import datetime, timezone
    try:
        from twisterlab.agents.registry import AgentRegistry
        registry = AgentRegistry()
        notion_agent = registry.get_agent("notion")
        
        if not notion_agent:
            return {"status": "error", "message": "Notion agent not found in registry"}
            
        result = await notion_agent.handle_list_pages(limit=15)
        
        if not result.success:
            return {"status": "error", "message": result.error}
            
        return {
            "status": "success",
            "data": result.data.get("pages", []),
            "count": result.data.get("count", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard Notion sync error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/dashboard/services")
async def dashboard_services():
    """Probe connectivity of key TwisterLab services."""
    N8N_URL = os.getenv("N8N_URL", "http://192.168.0.30:5678")
    probes = [
        {
            "name": "API Bridge",
            "url": "http://localhost:8000/api/v1/system/health",
            "port": 8000,
            "label": "api",
        },
        {
            "name": "n8n Engine",
            "url": f"{N8N_URL}/healthz",
            "port": 5678,
            "label": "n8n",
        },
        {
            "name": "Grafana",
            "url": "http://192.168.0.30:30091/api/health",
            "port": 30091,
            "label": "grafana",
        },
        {
            "name": "Prometheus",
            "url": "http://192.168.0.30:30090/-/ready",
            "port": 30090,
            "label": "prometheus",
        },
    ]
    results = []
    async with httpx.AsyncClient(timeout=2.0) as client:
        for svc in probes:
            try:
                r = await client.get(svc["url"])
                status = "up" if r.status_code < 500 else "degraded"
            except Exception:
                status = "down"
            results.append(
                {
                    "name": svc["name"],
                    "port": svc["port"],
                    "label": svc["label"],
                    "status": status,
                }
            )
    return {"services": results}

@app.get("/api/dashboard/n8n")
async def dashboard_n8n():
    """Fetch n8n workflows and recent executions via REST API."""
    N8N_URL = os.getenv("N8N_URL", "http://192.168.0.30:5678")
    api_key = os.getenv("N8N_API_KEY", "")
    headers = {}
    if api_key:
        headers["X-N8N-API-KEY"] = api_key

    try:
        async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
            wf_r = await client.get(f"{N8N_URL}/api/v1/workflows")
            ex_r = await client.get(f"{N8N_URL}/api/v1/executions?limit=15")

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
                executions = d.get("data", [])

            return {
                "status": "online",
                "auth_required": auth_required,
                "api_key_configured": bool(api_key),
                "workflows": workflows,
                "executions": executions,
            }
    except Exception as e:
        return {"status": "offline", "error": str(e), "workflows": [], "executions": []}


# --- N8N REVERSE PROXY (STRICTOR) ---

N8N_URL = os.getenv("N8N_URL", "http://192.168.0.30:5678")

async def _do_proxy(base_url: str, path: str, request: Request):
    # Strict Host Validation
    if not str(base_url).startswith(str(N8N_URL)):
         raise HTTPException(status_code=403, detail="Proxy target not allowed")
    url = f"{base_url}/{path}"
    query_params = str(request.query_params)
    if query_params:
        url += f"?{query_params}"

    async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
        headers = dict(request.headers)
        headers.pop("host", None)
        headers["accept-encoding"] = "identity"

        try:
            req = client.build_request(
                method=request.method,
                url=url,
                headers=headers,
                content=await request.body(),
            )
            res = await client.send(req, stream=True)

            if res.status_code in (301, 302, 303, 307, 308):
                location = res.headers.get("location", "")
                if location.startswith("/"):
                    new_location = f"/api/proxy/n8n{location}"
                    return RedirectResponse(new_location, status_code=res.status_code)
                return RedirectResponse(location, status_code=res.status_code)

            response_headers = dict(res.headers)
            for h in [
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "connection",
            ]:
                response_headers.pop(h, None)

            headers_to_remove = [
                "x-frame-options",
                "content-security-policy",
                "x-content-type-options",
                "x-xss-protection",
                "strict-transport-security",
            ]
            final_headers = {}
            for k, v in response_headers.items():
                if k.lower() not in headers_to_remove:
                    final_headers[k] = v

            final_headers["X-Frame-Options"] = "ALLOWALL"
            final_headers["Content-Security-Policy"] = "frame-ancestors 'self' *"

            content_type = final_headers.get("content-type", "").lower()

            if "text/html" in content_type:
                raw_content = await res.aread()
                body = raw_content.decode("utf-8", errors="ignore")
                import re
                body = re.sub(r"https?://localhost:\d+/?", "/api/proxy/n8n/", body)
                body = re.sub(r"https?://127\.0\.0\.1:\d+/?", "/api/proxy/n8n/", body)
                if "<head>" in body:
                    body = body.replace(
                        "<head>", '<head><base href="/api/proxy/n8n/">'
                    )
                return FastAPIResponse(
                    content=body.encode("utf-8"),
                    status_code=res.status_code,
                    headers=final_headers,
                    media_type=content_type,
                )

            return StreamingResponse(
                res.aiter_raw(),
                status_code=res.status_code,
                headers=final_headers,
                media_type=content_type,
            )
        except Exception as e:
            return FastAPIResponse(
                content=json.dumps({"error": "Gateway Timeout", "details": str(e)}),
                status_code=504,
                media_type="application/json",
            )


@app.api_route(
    "/api/proxy/n8n/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy_n8n(path: str, request: Request):
    return await _do_proxy(N8N_URL, path, request)


# --- CORTEX AI ---

async def _call_ollama(prompt: str, model: str = "llama3.2:1b") -> str:
    OLLAMA_URLS = [
        os.getenv("OLLAMA_BASE_URL", "http://192.168.0.30:11434"),
        "http://192.168.0.30:11434",
    ]
    payload = {"model": model, "prompt": prompt, "stream": False}
    for url in OLLAMA_URLS:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(f"{url}/api/generate", json=payload)
                if r.status_code == 200:
                    return r.json().get("response", "").strip()
        except:
            continue
    raise RuntimeError("Ollama unreachable")


@app.post("/api/dashboard/cortex")
async def cortex_chat(request: Request):
    try:
        body = await request.json()
        input_text = body.get("input") or ""
        text = await _call_ollama(f"Utilisateur: {input_text}\nCortex:")
        return {"content": [{"text": text}], "isError": False}
    except Exception as e:
        return {"content": [{"text": f"? Erreur: {str(e)}"}], "isError": True}


@app.get("/api/v1/system/ready", tags=["system"])
async def readiness_check():
    """
    Deep health check for Kubernetes Readiness Probes.
    Verifies Registry and critical service connectivity.
    """
    checks = {
        "registry": False,
        "database": False,
        "cache": False,
    }
    
    # 1. Registry Check
    try:
        from twisterlab.agents.registry import get_agent_registry
        reg = get_agent_registry()
        status = reg.get_registry_status()
        checks["registry"] = status["total"] > 0
    except Exception as e:
        logger.error(f"Readiness: Registry check failed: {e}")

    # 2. Database Check
    try:
        from twisterlab.database.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        logger.error(f"Readiness: Database check failed: {e}")

    # 3. Cache Check
    try:
        from twisterlab.database.session import engine # Fallback check if redis not found
        # In this env, let's look for redis in twisterlab.cache
        try:
             from twisterlab.cache.redis_client import get_redis_client
             redis = get_redis_client()
             if await redis.ping():
                 checks["cache"] = True
        except (ImportError, ModuleNotFoundError):
             # If redis module is missing, we might be in a dev env without it
             logger.warning("Readiness: Redis module missing, skipping cache check")
             checks["cache"] = True # Don't fail readiness in dev if redis is optional
    except Exception as e:
        logger.error(f"Readiness: Cache check failed: {e}")
    is_ready = all(checks.values())
    status_code = 200 if is_ready else 503
    
    return FastAPIResponse(
        status_code=status_code,
        content=json.dumps({
            "status": "ready" if is_ready else "not_ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }),
        media_type="application/json"
    )


@app.get("/health")
async def simple_health():
    """Liveness probe - just checks if the process is alive."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# --- ROOT & STATIC ---

@app.get("/")
async def root():
    root_path = Path(__file__).resolve().parents[3]
    index_path = root_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to TwisterLab API"}


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


# Mount the simple UI (if present)
pkg_ui = Path(__file__).resolve().parents[1] / "ui" / "browser"
generic_ui = Path(__file__).resolve().parents[2] / "ui" / "browser"
STATIC_UI = pkg_ui if pkg_ui.exists() else generic_ui
if STATIC_UI.exists():
    app.mount("/ui", StaticFiles(directory=str(STATIC_UI), html=True), name="ui")


# Metrics are handled via prometheus_fastapi_instrumentator in lifespan

# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return FastAPIResponse(
        status_code=exc.status_code,
        content=json.dumps({"detail": exc.detail}),
        media_type="application/json"
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = str(uuid.uuid4())
    logger.error(f"Unhandled Exception [trace_id={trace_id}]: {exc}", exc_info=True)
    
    error_msg = "Internal server error"
    debug_data = None
    
    if DEBUG:
        error_msg = str(exc)
        import traceback
        debug_data = {
            "traceback": traceback.format_exc(),
            "path": request.url.path,
        }
    
    response = MCPResponse(
        status="error",
        content=[{"type": "text", "text": f"Error: {error_msg}"}],
        isError=True,
        trace_id=trace_id,
        debug=debug_data,
        code="INTERNAL_ERROR"
    )
    
    return FastAPIResponse(
        status_code=500,
        content=response.model_dump_json(exclude_none=True),
        media_type="application/json"
    )
