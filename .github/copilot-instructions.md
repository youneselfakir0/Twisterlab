# TwisterLab Copilot Instructions

## Project Overview
TwisterLab is a cloud-native autonomous AI agent orchestration platform. Agents communicate via **TwisterLang** protocol, expose capabilities via **MCP (Model Context Protocol)** for IDE integration, and run on Kubernetes with full observability.

## Architecture Fundamentals

### Agent System
- **Base Class**: All agents inherit from `TwisterAgent` in `src/twisterlab/agents/base.py`
- **Registry Pattern**: `AgentRegistry` (singleton) in `src/twisterlab/agents/registry.py` manages all agent instances
- **Agent Types**: Maestro (orchestrator), Classifier, Resolver, Monitoring, Backup, Sync, DesktopCommander, Browser
- **Multi-Framework Export**: Agents export schemas to Microsoft Agent Framework, LangChain, Semantic Kernel, OpenAI Assistants via `.to_schema(format="microsoft")`
- **Real vs Mock**: "Real" agents (`src/twisterlab/agents/real/`) contain production logic; hybrid/mock modes exist for testing

### Database & Async Patterns
- **Critical**: Uses SQLAlchemy **async engine** exclusively (`create_async_engine`)
- **DATABASE_URL**: Must use async drivers: `sqlite+aiosqlite://` or `postgresql+asyncpg://`
- **Session**: Import from `twisterlab.database.session` → `AsyncSessionLocal`, `get_db()`
- **Auto-init**: Tables created on app startup in `src/twisterlab/api/main.py` lifespan
- **Models**: Defined in `src/twisterlab/database/models/` (e.g., `agent.py`)

### TwisterLang Protocol
- **Location**: `src/twisterlang/codec.py` (note: separate package, not `twisterlab.twisterlang`)
- **Message Structure**: `{"twisterlang_version": "1.0", "correlation_id": "<uuid>", "payload": {...}}`
- **Functions**: `build_message()`, `validate_message()`, `encode_message_to_base64()`, `decode_message_from_base64()`
- **Usage**: For inter-agent communication and MCP tool payloads

### MCP (Model Context Protocol)
- **Server**: `src/twisterlab/agents/mcp/mcp_server.py` → `MCPServerContinue` class
- **Entry Point**: `mcp_server_production.py` (stdio transport for Claude Desktop/Continue)
- **API Routes**: `src/twisterlab/api/routes_mcp_real.py` exposes 39 MCP tools as REST endpoints
- **Tools**: `list_autonomous_agents`, `classify_ticket`, `resolve_ticket`, `monitor_system_health`, etc.
- **Mode Detection**: Auto-switches REAL/HYBRID based on API connectivity test

## Development Workflows

### Running the API Locally
```powershell
# With auto-reload (dev)
uvicorn src.twisterlab.api.main:app --reload --port 8000

# Access Swagger docs at http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

### Testing
```powershell
# Unit/integration tests (auto-discovers async tests)
pytest -q

# E2E Playwright tests (requires env var)
python -m playwright install --with-deps chromium
$env:E2E = '1'
pytest -q -m e2e
```

### Adding a New Agent
1. **Scaffold**: `python scripts/new_agent_scaffold.py --name MyAgent --llm llama-3.2`
2. **Implement**: Extend `TwisterAgent` in `src/twisterlab/agents/real/`
3. **Register**: Add to `AgentRegistry.initialize_agents()` in `registry.py`
4. **K8s Deployment**: Create manifest in `k8s/deployments/` if agent needs dedicated pod
5. **Expose via MCP**: Add route in `routes_mcp_real.py` calling `agent.execute(task, context)`

### Database Migrations
- **Tool**: Alembic (`alembic.ini`, `alembic/versions/`)
- **Create Migration**: `alembic revision -m "description"`
- **Apply**: `alembic upgrade head`

### Code Quality
```powershell
# Linting & formatting (enforced in CI)
ruff check src/twisterlab tests/
black src/twisterlab tests/
mypy src/twisterlab

# Or use pre-commit
pre-commit run --all-files
```

## Project-Specific Conventions

### Import Paths
- **TwisterLab Code**: `from twisterlab.agents.base import TwisterAgent`
- **TwisterLang Codec**: `from twisterlang.codec import build_message` (no `.twisterlab` prefix)
- **Path Setup**: `conftest.py` adds `src/` to `sys.path` for tests

### Pydantic v2
- Use `.model_dump()` instead of deprecated `.dict()`
- Use `Field()` for schema definitions with validation

### API Route Organization
- **System**: `src/twisterlab/api/routes/system.py` (health, metrics)
- **Agents**: `src/twisterlab/api/routes/agents.py` (CRUD for agent metadata)
- **MCP Tools**: `src/twisterlab/api/routes_mcp_real.py` (agent execution endpoints)
- **Browser**: `src/twisterlab/api/routes/browser.py` (Playwright automation)

### Kubernetes Deployment
- **Namespace**: `twisterlab` (all resources)
- **Manifests**: `k8s/base/` (namespace, configs), `k8s/deployments/` (apps), `k8s/monitoring/` (Prometheus/Grafana)
- **Secrets**: `k8s/base/secrets.yaml` (DATABASE_URL, REDIS_URL stored here)
- **Ingress**: NGINX Ingress at `edgeserver.twisterlab.local:30001`

### Environment Variables
- `DATABASE_URL`: PostgreSQL or SQLite connection string (must use async driver)
- `REDIS_URL`: Redis cache/pub-sub endpoint
- `API_URL`: MCP server backend URL (default: `http://192.168.0.30:8000`)
- `MCP_LOG_LEVEL`: Logging verbosity for MCP server
- `E2E`: Set to `1` to enable Playwright E2E tests

## Common Pitfalls

### Async DB Engine
❌ **Wrong**: `create_engine("postgres://...")` (sync engine)  
✅ **Correct**: `create_async_engine("postgresql+asyncpg://...")` + `AsyncSessionLocal`

### TwisterLang Import
❌ **Wrong**: `from twisterlab.twisterlang.codec import ...`  
✅ **Correct**: `from twisterlang.codec import ...`

### Agent Lookup
- `AgentRegistry.get_agent()` is **forgiving**: handles hyphens, underscores, "agent" suffix variations
- Example: `get_agent("classifier")` == `get_agent("real-classifier")` == `get_agent("RealClassifierAgent")`

### Test Markers
- Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e` to categorize tests
- E2E tests only run when `E2E=1` environment variable is set

## Key Files Reference
- **API Entry**: `src/twisterlab/api/main.py` (FastAPI app, lifespan, metrics)
- **Agent Base**: `src/twisterlab/agents/base.py` (`TwisterAgent` abstract class)
- **Agent Registry**: `src/twisterlab/agents/registry.py` (singleton, all agents)
- **DB Session**: `src/twisterlab/database/session.py` (async engine, Base, get_db)
- **TwisterLang**: `src/twisterlang/codec.py` (protocol implementation)
- **MCP Server**: `mcp_server_production.py` + `src/twisterlab/agents/mcp/mcp_server.py`
- **Test Config**: `conftest.py`, `pytest.ini` (async mode, markers)
- **Dependencies**: `requirements.txt`, `pyproject.toml` (Pydantic v2, SQLAlchemy v2, FastAPI)
- **K8s Deployment**: `k8s/deployments/twisterlab-api.yaml` (main API deployment)
- **Docker Compose**: `docker-compose.yml` (local multi-service stack)

## Deployment Modes
1. **Local Dev**: `uvicorn` + Docker Compose (postgres, redis)
2. **Kubernetes**: k3s/minikube with Ingress + monitoring stack
3. **MCP Integration**: stdio transport via `mcp_server_production.py` for Claude Desktop/Continue

## Observability
- **Metrics**: Prometheus endpoint at `/metrics` (auto-instrumented via FastAPI Instrumentator)
- **Tracing**: OpenTelemetry support in `src/twisterlab/tracing.py`
- **Health Checks**: `/health` (liveness), `/system/status` (detailed)
- **Dashboards**: Grafana manifests in `k8s/monitoring/grafana/`