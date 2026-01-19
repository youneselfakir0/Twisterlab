# 🌀 TwisterLab - AI Agent Instructions

## Project Overview
**Multi-agent platform automating technical support**: tickets → analysis → resolution → prevention.
Maestro (LLM orchestrator) coordinates 10 specialized agents via MCP (Model Context Protocol).

## Architecture
```
TICKET → FastAPI → Maestro → Agents (Sentiment, Classifier, Monitoring, Browser, Commander, Resolver, Backup, Sync, CodeReview)
```

**Key paths:**
- `src/twisterlab/agents/real/` - 10 production agents (TwisterAgent-based)
- `src/twisterlab/agents/core/base.py` - Base classes: `TwisterAgent`, `AgentCapability`, `AgentResponse`
- `src/twisterlab/agents/registry.py` - Singleton `AgentRegistry` with flexible lookup
- `src/twisterlab/api/main.py` - FastAPI app entry point
- `src/twisterlab/database/session.py` - Async SQLAlchemy sessions

## Critical Patterns

### ⚠️ Database - ALWAYS Async
```python
# ❌ BREAKS THE APP
from sqlalchemy import create_engine
DATABASE_URL = "postgresql://..."

# ✅ REQUIRED
from sqlalchemy.ext.asyncio import create_async_engine
DATABASE_URL = "postgresql+asyncpg://..."

# Import session correctly
from twisterlab.database.session import AsyncSessionLocal, get_db
```

### ⚠️ Pydantic v2
```python
# ❌ Old syntax
model.dict()
# ✅ Correct
model.model_dump()
```

### Agent Lookup (flexible matching)
```python
from twisterlab.agents.registry import agent_registry
agent = agent_registry.get_agent("classifier")        # Works
agent = agent_registry.get_agent("real-classifier")  # Works
agent = agent_registry.get_agent("monitoring")       # Works (fuzzy)
```

## Creating a New Agent

1. **Scaffold**: `python scripts/new_agent_scaffold.py --name MyAgent`

2. **Implement** (`src/twisterlab/agents/real/my_agent.py`):
```python
from twisterlab.agents.core.base import (
    TwisterAgent, AgentCapability, AgentResponse,
    CapabilityType, CapabilityParam, ParamType
)

class MyAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "my-agent"
    
    @property
    def description(self) -> str:
        return "What the agent does"
    
    def get_capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="action_name",
                description="Action description",
                handler="handle_action",
                capability_type=CapabilityType.ACTION,
                params=[CapabilityParam("input", ParamType.STRING, "Description", required=True)]
            )
        ]
    
    async def handle_action(self, input: str) -> AgentResponse:
        return AgentResponse(success=True, data={"result": input})
```

3. **Register** in `src/twisterlab/agents/registry.py` → `initialize_agents()`

4. **Test** (`tests/unit/test_my_agent.py`):
```python
pytestmark = pytest.mark.unit

class TestMyAgent:
    @pytest.fixture
    def agent(self):
        return MyAgent()

    @pytest.mark.asyncio
    async def test_action(self, agent):
        result = await agent.handle_action("test")
        assert result.success is True
```

## Development Commands

```powershell
# Local dev
$env:PYTHONPATH="src"; uvicorn twisterlab.api.main:app --reload --port 8000

# Tests (use markers: unit, integration, e2e)
pytest tests/unit -v
pytest tests/integration -v
$env:E2E='1'; pytest -m e2e -v

# Linting (required before PR)
ruff check src tests; black src tests

# Docker
docker-compose -f docker-compose.production.yml up -d
docker-compose logs -f api

# Kubernetes
kubectl apply -f k8s/base/ k8s/deployments/
kubectl get pods -n twisterlab
```

## API Endpoints
- `/health`, `/ready` - K8s probes
- `/metrics` - Prometheus
- `/docs` - Swagger UI
- `/api/v1/mcp/tools/*` - MCP agent endpoints
- `/api/v1/agents` - List all agents

## Code Standards
- **Async everywhere** - All I/O operations
- **Type hints** - Strict typing with `-> AgentResponse`
- **Error handling** - Return `AgentResponse(success=False, error=str(e))`
- **Logging** - Use `logger.info(f"🚀 {self.name}: {action}")`

## Commit Format
```
feat(maestro): implement LLM decision engine
fix(browser): handle timeout gracefully
test(agents): add classifier edge cases
```

## Environment Variables
```bash
DATABASE_URL=postgresql+asyncpg://...  # MUST be asyncpg
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
PYTHONPATH=src
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
