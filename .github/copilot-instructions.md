# 🌀 TwisterLab - AI Agent Instructions

## Project Overview
**Multi-agent platform automating technical support**: tickets → analysis → resolution → prevention.
Maestro (LLM orchestrator) coordinates 20+ specialized agents via standardized MCP (Model Context Protocol).

TwisterLab v3.5.0 is **production-ready** with real agent implementations (not mocks), security hardening, and K8s HA deployment.

## Architecture (Data Flow)
```
TICKET → FastAPI REST/MCP → Agent Registry → Maestro → Specialized Agents (Sentiment, Classifier, Monitoring, etc.)
                                                      ↓
                                    Async Database (PostgreSQL + asyncpg)
```

**Key Architecture Layers:**
- **Transport**: FastAPI with native MCP support (Stdio & SSE) at `/api/v1/mcp/tools/*`
- **Orchestration**: Maestro Agent (LLM-powered) coordinates multi-agent workflows
- **Agent System**: Registry pattern with 20+ real production agents (ClassifierAgent, SentimentAnalyzerAgent, etc.)
- **Data Access**: Async SQLAlchemy with PostgreSQL (asyncpg driver required)
- **Protocol**: MCP (Model Context Protocol) bridges agents to LLM interfaces

**Key paths:**
- `src/twisterlab/agents/real/` - 20+ production agents (all TwisterAgent-based)
- `src/twisterlab/agents/core/base.py` - Base classes: `CoreAgent`, `TwisterAgent`, `AgentCapability`, `AgentResponse`
- `src/twisterlab/agents/registry.py` - Singleton `AgentRegistry` with flexible name-matching lookup
- `src/twisterlab/api/main.py` - FastAPI app entry point with lifespan manager
- `src/twisterlab/api/routes_mcp_real.py` - MCP endpoint handlers
- `src/twisterlab/database/session.py` - Async SQLAlchemy engine + session factory

## Critical Patterns & Design Decisions

### ⚠️ Database - ALWAYS Async (Non-Negotiable)
```python
# ❌ BREAKS THE APP - synchronous driver
from sqlalchemy import create_engine
DATABASE_URL = "postgresql://..."  # WRONG!

# ✅ REQUIRED - async driver (asyncpg)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
DATABASE_URL = "postgresql+asyncpg://..."

# Auto-conversion in session.py handles old-style postgres:// URLs
if DATABASE_URL.startswith("postgres"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")

# Import session correctly
from twisterlab.database.session import AsyncSessionLocal, get_db
async with AsyncSessionLocal() as db:
    result = await db.execute(...)
```
**Why**: FastAPI is async-first. Sync engines block the entire event loop, causing request timeouts and K8s probe failures.

### ⚠️ Pydantic v2 Syntax (Required)
```python
# ❌ Old Pydantic v1
model.dict()
model.json()

# ✅ Pydantic v2
model.model_dump()          # Returns dict
model.model_dump_json()     # Returns JSON string
```

### Agent Base Classes (Two Patterns)

**CoreAgent** (abstract base for all agents):
```python
from twisterlab.agents.core.base import CoreAgent

class MyAgent(CoreAgent):
    @property
    def name(self) -> str:
        return "my-agent"
    
    @property
    def description(self) -> str:
        return "Does X, Y, Z"
```

**TwisterAgent** (common convenience, extends CoreAgent):
- Pre-configured logging with `self.logger`
- Pre-configured service registry access via `self.service_registry`
- Use this unless you need minimal base class

Both must implement:
- `name: str` property
- `description: str` property
- `get_capabilities() -> list[AgentCapability]` method
- Handler methods (async or sync) that return `AgentResponse`

### Agent Registry Lookup (Flexible Matching)
```python
from twisterlab.agents.registry import agent_registry

# All these work due to normalized name matching:
agent = agent_registry.get_agent("classifier")         # Exact
agent = agent_registry.get_agent("real-classifier")    # Hyphen removed
agent = agent_registry.get_agent("realclassifier")     # Underscore/space removed
agent = agent_registry.get_agent("CLASSIFIER")         # Case-insensitive

# Priority resolution: Higher priority agents win in conflicts
# Archive agent priority=20 (preferred), others=10
```

### Agent Capabilities Structure
Every agent declares what it can do via `get_capabilities()`:
```python
def get_capabilities(self) -> List[AgentCapability]:
    return [
        AgentCapability(
            name="action_name",                    # Tool name for LLM
            description="Analyzes ticket...",     # LLM sees this
            handler="handle_action",              # Method name on agent
            capability_type=CapabilityType.QUERY, # QUERY (read-only) or ACTION (mutating)
            params=[
                CapabilityParam(
                    "ticket_id", 
                    ParamType.STRING, 
                    "Ticket ID to analyze", 
                    required=True
                )
            ]
        )
    ]

async def handle_action(self, ticket_id: str) -> AgentResponse:
    try:
        result = ... # business logic
        return AgentResponse(success=True, data={"result": result})
    except Exception as e:
        return AgentResponse(success=False, error=str(e))
```

### MCP Response Format
All agent handlers return `AgentResponse`, which MCP adapter converts to MCP content:
```python
# Agent returns this
AgentResponse(success=True, data={"category": "DATABASE", "priority": "high"})

# MCP converts to this for LLM
{
  "type": "text",
  "text": "{\"category\": \"DATABASE\", \"priority\": \"high\"}"
}

# Errors auto-convert
AgentResponse(success=False, error="Service unavailable")
# → {"type": "text", "text": "Error: Service unavailable"}
```

## Creating a New Agent (5-Step Process)

### Step 1: Generate Scaffold
```powershell
python scripts/new_agent_scaffold.py --name MyCustomAgent
# Creates: src/twisterlab/agents/real/my_custom_agent.py
```

### Step 2: Implement Core Methods
```python
# src/twisterlab/agents/real/my_custom_agent.py
from twisterlab.agents.core.base import (
    TwisterAgent, AgentCapability, AgentResponse,
    CapabilityType, CapabilityParam, ParamType
)

class MyCustomAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "my-custom"  # Lookup name (auto-normalized)
    
    @property
    def description(self) -> str:
        return "Performs custom analysis or actions"
    
    def get_capabilities(self) -> list[AgentCapability]:
        """Define what this agent can do."""
        return [
            AgentCapability(
                name="analyze_data",
                description="Analyzes input data and returns insights",
                handler="handle_analyze",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("data", ParamType.STRING, "Input data", required=True),
                    CapabilityParam("mode", ParamType.STRING, "Analysis mode", 
                                   required=False, enum=["quick", "deep"])
                ]
            )
        ]
    
    async def handle_analyze(self, data: str, mode: str = "quick") -> AgentResponse:
        """Handler for 'analyze_data' capability."""
        try:
            # ✅ Use self.logger for consistent logging
            self.logger.info(f"🔍 Analyzing data in {mode} mode")
            
            # Your business logic here
            result = self._process(data, mode)
            
            return AgentResponse(success=True, data={"insights": result})
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    def _process(self, data: str, mode: str) -> dict:
        """Internal helper - not exposed as capability."""
        # Your implementation
        return {"summary": "...", "score": 0.85}
```

### Step 3: Register in Agent Registry
Edit `src/twisterlab/agents/registry.py` → `_register_default_factories()`:
```python
registry_data = [
    # ... existing agents ...
    ("my-custom", "twisterlab.agents.real.my_custom_agent", "MyCustomAgent", 
     "Performs custom analysis", ["analyze_data"], 10),  # priority=10
]
```

### Step 4: Write Unit Tests
```python
# tests/unit/agents/test_my_custom_agent.py
import pytest
from twisterlab.agents.real.my_custom_agent import MyCustomAgent

pytestmark = pytest.mark.unit

class TestMyCustomAgent:
    @pytest.fixture
    def agent(self):
        return MyCustomAgent()
    
    @pytest.mark.asyncio
    async def test_analyze_quick_mode(self, agent):
        result = await agent.handle_analyze("test data", mode="quick")
        assert result.success is True
        assert "insights" in result.data
    
    @pytest.mark.asyncio
    async def test_analyze_error_handling(self, agent):
        result = await agent.handle_analyze("")  # Invalid input
        assert result.success is False
        assert result.error is not None
```

### Step 5: Verify Integration
```powershell
# 1. Test agent loads via registry
pytest tests/unit/agents/test_my_custom_agent.py -v

# 2. Run E2E to verify MCP integration
$env:E2E='1'; pytest tests/e2e/test_mcp_integration.py -v -k my_custom

# 3. Test in local dev server
$env:PYTHONPATH="src"; uvicorn twisterlab.api.main:app --reload
# Visit http://localhost:8000/docs → /api/v1/mcp/tools/list_autonomous_agents
```

**Common Agent Patterns:**
- **Query Agent** (read-only): Classification, sentiment analysis, monitoring → `CapabilityType.QUERY`
- **Action Agent** (mutating): Database writes, command execution, backups → `CapabilityType.ACTION`
- **Streaming Agent** (large output): Image generation, long text processing → `CapabilityType.STREAM`

## Development Workflows & Commands

### Quick Start (Local Development)
```powershell
# 1. Set Python path (Windows PowerShell)
$env:PYTHONPATH="src"

# 2. Install dependencies
poetry install  # or: pip install -r requirements.txt

# 3. Start API with auto-reload
uvicorn twisterlab.api.main:app --reload --port 8000

# 4. Access interactive docs
# Visit: http://localhost:8000/docs
```

### Testing (Use Pytest Markers)
```powershell
# Unit tests (fast, isolated, no DB/network)
pytest tests/unit -v
pytest tests/unit/agents/test_my_custom_agent.py -v  # Single test file

# Integration tests (with real services, slower)
pytest tests/integration -v

# End-to-end tests (full stack, k8s probes, etc.)
$env:E2E='1'; pytest -m e2e -v

# Run specific test by name
pytest -k "test_classify" -v

# With coverage report
pytest tests/unit --cov=src/twisterlab --cov-report=html
```

### Code Quality (Required Before PR)
```powershell
# Lint with ruff (fast)
ruff check src tests

# Format with black
black src tests

# Type checking with mypy (optional but recommended)
mypy src --ignore-missing-imports

# All in one
ruff check src tests; black src tests
```

### Docker & Kubernetes
```powershell
# Build and run production stack
docker-compose -f docker-compose.production.yml up -d

# Check container logs
docker-compose logs -f api

# Kubernetes deployment
kubectl apply -f k8s/base/ k8s/deployments/
kubectl get pods -n twisterlab
kubectl logs -f -n twisterlab deployment/twisterlab-api

# Port forward for local debugging
kubectl port-forward -n twisterlab svc/twisterlab-api 8000:8000
```

### Database Operations
```powershell
# Run migrations (Alembic)
alembic upgrade head

# Generate new migration after schema change
alembic revision --autogenerate -m "Add user_role column"

# Check current migration status
alembic current
```

### Debugging Tips
- **Log rotation**: Check `logs/` directory for persistent logs
- **MCP protocol debugging**: Add `--log-level=DEBUG` to uvicorn command
- **Database pool issues**: Check `AsyncSessionLocal` in `src/twisterlab/database/session.py`
- **Agent registration**: Use `/api/v1/mcp/tools/list_autonomous_agents` endpoint to verify

## API Endpoints Reference
- `/health` - Basic health check
- `/ready` - Kubernetes readiness probe (includes agent registry check)
- `/metrics` - Prometheus metrics for monitoring
- `/docs` - Interactive Swagger UI (auto-generated from FastAPI)
- `/api/v1/mcp/tools/list_autonomous_agents` - List all available agents + capabilities
- `/api/v1/mcp/tools/call_agent_tool` - Execute agent capability (main MCP tool endpoint)
- `/api/v1/agents` - List agent metadata

### Testing an Agent Capability via API
```bash
# 1. Get agent list
curl http://localhost:8000/api/v1/mcp/tools/list_autonomous_agents | jq

# 2. Call agent tool (POST request)
curl -X POST http://localhost:8000/api/v1/mcp/tools/call_agent_tool \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "classifier",
    "tool_name": "classify_ticket",
    "input": {"ticket_text": "Database is down"}
  }'

# 3. Response format
# {"content": [{"type": "text", "text": "{\"category\": \"DATABASE\", \"priority\": \"high\"}"}]}
```

## Code Standards
- **Async everywhere** - All I/O operations must be async (database, network, file)
- **Type hints** - Strict typing with `-> AgentResponse` or other return types
- **Error handling** - Always return `AgentResponse(success=False, error=str(e))`
- **Logging** - Use `logger.info(f"🚀 {self.name}: {action}")` with emoji for visibility
- **No hardcoded values** - Use environment variables for config (DATABASE_URL, etc.)
- **Docstrings** - Every method/class gets docstrings describing purpose, args, return
- **Agent response format** - All handlers MUST return `AgentResponse`, not raw values

**❌ Bad Examples:**
```python
# Mixing sync/async
result = requests.get(url)  # WRONG - should be httpx or aiohttp

# Missing error handling
return AgentResponse(success=True, data=risky_operation())

# Hardcoded values
DATABASE_URL = "postgresql://localhost/mydb"

# No logging
return result
```

**✅ Good Examples:**
```python
# Async all the way
async with httpx.AsyncClient() as client:
    result = await client.get(url)

# Proper error handling
try:
    result = await risky_operation()
    return AgentResponse(success=True, data=result)
except Exception as e:
    self.logger.error(f"Operation failed: {e}")
    return AgentResponse(success=False, error=str(e))

# Environment-based config
DATABASE_URL = os.environ.get("DATABASE_URL", "...")

# Informative logging
self.logger.info(f"🔍 {self.name}: Classifying ticket {ticket_id}")
```

## Commit Format (Conventional Commits)
```
feat(maestro): implement LLM decision engine
fix(browser): handle timeout gracefully
test(agents): add classifier edge cases
docs(readme): update installation steps
refactor(registry): simplify agent lookup
```

## Environment Variables
```bash
DATABASE_URL=postgresql+asyncpg://...  # MUST be asyncpg, not postgres://
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
PYTHONPATH=src
LOG_LEVEL=INFO
```

## Key Files Reference
| Purpose | File |
|---------|------|
| Agent base class | `src/twisterlab/agents/core/base.py` |
| Agent registry | `src/twisterlab/agents/registry.py` |
| DB session | `src/twisterlab/database/session.py` |
| API main | `src/twisterlab/api/main.py` |
| Pytest config | `pytest.ini` |
| Example agent | `src/twisterlab/agents/real/real_monitoring_agent.py`
