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

## CI/CD Pipeline

### GitHub Actions Workflows
- **CI**: `.github/workflows/ci.yml` - Runs on every push/PR
  - Linting (ruff, mypy, black)
  - Unit & integration tests (pytest)
  - Code coverage report
- **CD**: `.github/workflows/cd.yml` - Deploys on merge to main
  - Builds Docker images (`Dockerfile.api`, `Dockerfile.mcp`)
  - Pushes to container registry
  - Updates K8s deployments
- **Security**: `.github/workflows/security.yml` - Daily scans
  - Dependency vulnerability scanning
  - Secret detection (`scripts/scan_secrets.py`)

### Container Images
```powershell
# Build all images
docker build -t twisterlab-api:latest -f Dockerfile.api .
docker build -t twisterlab-mcp:latest -f Dockerfile.mcp .
docker build -t twisterlab-mcp-unified:latest -f Dockerfile.mcp-unified .

# Local stack with Docker Compose
docker-compose up -d                    # Main services
docker-compose -f docker-compose.postgres.yml up -d  # PostgreSQL only
docker-compose -f docker-compose.observability.yml up -d  # Monitoring stack
```

## Production Deployment

### Kubernetes Deployment Strategy
```powershell
# Deploy to K8s cluster
kubectl apply -f k8s/base/              # Namespace, ConfigMaps, Secrets
kubectl apply -f k8s/deployments/       # Application deployments
kubectl apply -f k8s/monitoring/        # Prometheus & Grafana

# Verify deployment
kubectl get pods -n twisterlab
kubectl logs -f deployment/twisterlab-api -n twisterlab

# Rolling update
kubectl set image deployment/twisterlab-api twisterlab-api=twisterlab-api:v2.0 -n twisterlab
kubectl rollout status deployment/twisterlab-api -n twisterlab

# Rollback if needed
kubectl rollout undo deployment/twisterlab-api -n twisterlab
```

### Resource Management
- **CPU/Memory Limits**: Defined in each deployment YAML
  - API: 1 CPU / 1Gi memory (request), 2 CPU / 2Gi (limit)
  - MCP: 500m CPU / 512Mi memory (request), 1 CPU / 1Gi (limit)
- **Auto-scaling**: HPA configured for API pods (min: 2, max: 10)
- **PersistentVolumes**: PostgreSQL uses PVC with 10Gi storage

### Ingress & Networking
- **Ingress Controller**: NGINX Ingress
- **Host**: `edgeserver.twisterlab.local:30001`
- **TLS**: Configure cert-manager for production HTTPS
- **Internal Services**: ClusterIP for inter-service communication

## Security Best Practices

### Secrets Management
- **Development**: Use `.env` files (never commit!)
- **Kubernetes**: Store in `k8s/base/secrets.yaml` (base64 encoded)
- **Production**: Use external secret managers:
  - Azure Key Vault (preferred for Azure)
  - HashiCorp Vault
  - AWS Secrets Manager

### Secret Detection
```powershell
# Scan for secrets before commit
python scripts/scan_secrets.py

# Uses detect-secrets + gitleaks
# Configure in .pre-commit-config.yaml
```

### Database Credentials
```yaml
# k8s/base/secrets.yaml (example structure)
apiVersion: v1
kind: Secret
metadata:
  name: twisterlab-secrets
  namespace: twisterlab
type: Opaque
data:
  DATABASE_URL: <base64-encoded-connection-string>
  REDIS_URL: <base64-encoded-redis-url>
```

## Backup & Disaster Recovery

### Database Backup Agent
- **Automated**: `RealBackupAgent` in `src/twisterlab/agents/real/real_backup_agent.py`
- **Schedule**: Configurable via K8s CronJob
- **Storage**: PostgreSQL dumps to S3-compatible storage
- **Retention**: 30 days (configurable)

### Recovery Procedure
```powershell
# Restore from backup
kubectl exec -it deployment/postgres -n twisterlab -- psql -U twisterlab < backup.sql

# Verify data integrity
kubectl exec -it deployment/twisterlab-api -n twisterlab -- python -m twisterlab.scripts.verify_db
```

## Performance Optimization

### Database Performance
- **Connection Pooling**: SQLAlchemy async pool (default: 5-20 connections)
- **Indexes**: Defined in Alembic migrations for frequent queries
- **Query Optimization**: Use `.select()` with specific columns to avoid N+1 queries

### Redis Caching
- **Cache Strategy**: Write-through for agent state
- **TTL**: 1 hour for agent metadata, 5 minutes for system status
- **Invalidation**: Event-driven via pub/sub

### API Performance
```python
# Example: Efficient agent lookup with caching
from twisterlab.agents.registry import AgentRegistry

registry = AgentRegistry()  # Singleton - reuses instances
agent = registry.get_agent("classifier")  # O(1) lookup
```

## Monitoring & Alerting

### Prometheus Metrics
- **Custom Metrics**: Defined in `src/twisterlab/monitoring.py`
  - `twisterlab_agent_execution_seconds` (histogram)
  - `twisterlab_agent_errors_total` (counter)
  - `twisterlab_mcp_requests_total` (counter)
- **Scrape Config**: `k8s/monitoring/prometheus/prometheus-config.yaml`

### Grafana Dashboards
- **Pre-built**: Import from `k8s/monitoring/grafana/dashboards/`
  - System Overview (CPU, Memory, Network)
  - Agent Performance (execution time, success rate)
  - MCP Tools Usage

### Alerting Rules
```yaml
# Example alert: High error rate
- alert: HighAgentErrorRate
  expr: rate(twisterlab_agent_errors_total[5m]) > 0.1
  for: 5m
  annotations:
    summary: "Agent {{ $labels.agent_name }} error rate is high"
```

## Troubleshooting Guide

### Common Issues

#### API Not Starting
```powershell
# Check logs
kubectl logs deployment/twisterlab-api -n twisterlab --tail=100

# Common causes:
# 1. Database connection failed → Verify DATABASE_URL in secrets
# 2. Port already in use → Check for conflicting services
# 3. Missing migrations → Run: alembic upgrade head
```

#### MCP Tools Not Responding
```powershell
# Verify MCP server connectivity
curl http://192.168.0.30:8000/health

# Check mode (should be REAL, not HYBRID)
kubectl logs deployment/mcp-unified -n twisterlab | grep "Mode:"

# Test specific tool
curl -X POST http://192.168.0.30:8000/mcp/list_autonomous_agents
```

#### Agent Execution Failures
```python
# Debug agent execution
from twisterlab.agents.registry import AgentRegistry

registry = AgentRegistry()
agent = registry.get_agent("classifier")
result = await agent.execute("test task", {"debug": True})
print(result)
```

#### Database Migration Issues
```powershell
# Check current migration version
alembic current

# Show migration history
alembic history

# Downgrade one version if needed
alembic downgrade -1

# Re-apply
alembic upgrade head
```

### Performance Debugging
```powershell
# Enable detailed logging
$env:LOG_LEVEL = "DEBUG"
uvicorn src.twisterlab.api.main:app --reload --port 8000

# Profile API endpoints
python -m cProfile -o profile.stats -m uvicorn src.twisterlab.api.main:app

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats
```

## Development Environment Setup

### Windows (PowerShell)
```powershell
# Clone and setup
git clone https://github.com/youneselfakir0/twisterlab.git
cd twisterlab

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install dev tools
pip install pre-commit
pre-commit install

# Setup local database
docker-compose -f docker-compose.postgres.yml up -d

# Run migrations
alembic upgrade head

# Start API
uvicorn src.twisterlab.api.main:app --reload --port 8000
```

### Linux/macOS
```bash
# Clone and setup
git clone https://github.com/youneselfakir0/twisterlab.git
cd twisterlab

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install dev tools
pip install pre-commit
pre-commit install

# Setup local database
docker-compose -f docker-compose.postgres.yml up -d

# Run migrations
alembic upgrade head

# Start API
uvicorn src.twisterlab.api.main:app --reload --port 8000
```

## Multi-Environment Configuration

### Environment Files
- `config/environments/development.env` - Local development
- `config/environments/staging.env` - Pre-production testing
- `config/environments/production.env` - Production (never commit!)

### Loading Environment
```powershell
# Development
$env:TWISTERLAB_ENV = "development"
python -m dotenv -f config/environments/development.env run uvicorn src.twisterlab.api.main:app

# Staging
$env:TWISTERLAB_ENV = "staging"
kubectl apply -f k8s/overlays/staging/

# Production
$env:TWISTERLAB_ENV = "production"
kubectl apply -f k8s/overlays/production/
```

## Load Testing

### Using k6
```javascript
// load-test.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
};

export default function () {
  let res = http.get('http://192.168.0.30:8000/health');
  check(res, { 'status is 200': (r) => r.status === 200 });
}
```

```powershell
# Run load test
k6 run load-test.js
```

## Documentation

### Generate API Docs
```powershell
# Swagger UI available at /docs
# ReDoc available at /redoc
# OpenAPI schema at /openapi.json

# Export OpenAPI spec
curl http://localhost:8000/openapi.json > api-spec.json
```

### Architecture Diagrams
- Located in `docs/architecture/`
- Generate with PlantUML or Mermaid
- Keep synchronized with code changes

## DevOps Best Practices for TwisterLab

### Infrastructure as Code (IaC)
- **All infrastructure in Git**: K8s manifests, Docker Compose files, scripts
- **Version everything**: Tag Docker images with Git commit SHA or semantic version
- **Declarative approach**: Use K8s manifests, avoid imperative kubectl commands in production

### GitOps Workflow
```powershell
# Feature development
git checkout -b feature/new-agent
# ... make changes ...
git commit -m "feat(agents): add sentiment analysis agent"
git push origin feature/new-agent
# Create PR → CI runs tests → Merge → CD deploys

# Hotfix workflow
git checkout -b hotfix/api-timeout
# ... fix issue ...
git commit -m "fix(api): increase request timeout to 60s"
git push origin hotfix/api-timeout
# Create PR → Fast-track review → Deploy
```

### Deployment Best Practices
1. **Blue-Green Deployments**: Use K8s rolling updates with readiness probes
2. **Canary Releases**: Deploy to 10% of pods first, monitor, then full rollout
3. **Immutable Infrastructure**: Never SSH into pods to make changes
4. **Config as Code**: All environment variables in ConfigMaps/Secrets

### Monitoring-First Approach
- **Instrument before deploying**: Add metrics to new features
- **Log structured data**: Use JSON logging for better parsing
- **Alert on symptoms, not causes**: Monitor user-facing metrics
- **SLOs/SLIs**: Define Service Level Objectives for critical paths

### Incident Response
```powershell
# 1. Acknowledge alert
# 2. Check runbook (docs/OPERATIONS/)
# 3. Gather context
kubectl get pods -n twisterlab
kubectl logs deployment/twisterlab-api -n twisterlab --since=1h

# 4. Quick mitigation (rollback if needed)
kubectl rollout undo deployment/twisterlab-api -n twisterlab

# 5. Root cause analysis
# 6. Post-mortem (blameless)
# 7. Update runbook
```

### Cost Optimization
- **Right-size resources**: Review CPU/memory usage monthly
- **Use autoscaling**: HPA for pods, cluster autoscaler for nodes
- **Optimize images**: Multi-stage Docker builds, Alpine base images
- **Clean up**: Remove unused images, PVs, and completed jobs

### Security Hardening
```yaml
# SecurityContext in deployment manifests
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

### Dependency Management
```powershell
# Pin dependencies for reproducibility
pip-compile requirements.in > requirements.txt

# Update dependencies safely
python scripts/update_dependencies.py

# Scan for vulnerabilities
pip-audit
```

## Quick Reference Commands

### Daily Operations
```powershell
# Check system health
curl http://edgeserver.twisterlab.local:30001/health

# View recent logs
kubectl logs -f deployment/twisterlab-api -n twisterlab --tail=50

# Restart a service
kubectl rollout restart deployment/twisterlab-api -n twisterlab

# Scale horizontally
kubectl scale deployment/twisterlab-api --replicas=5 -n twisterlab

# Execute command in pod
kubectl exec -it deployment/twisterlab-api -n twisterlab -- /bin/bash
```

### Debugging
```powershell
# Port forward for local debugging
kubectl port-forward deployment/twisterlab-api 8000:8000 -n twisterlab

# Check resource usage
kubectl top pods -n twisterlab
kubectl top nodes

# Describe pod for events
kubectl describe pod <pod-name> -n twisterlab

# Get all resources in namespace
kubectl get all -n twisterlab
```

### Database Operations
```powershell
# Connect to PostgreSQL
kubectl exec -it deployment/postgres -n twisterlab -- psql -U twisterlab -d twisterlab

# Create backup
kubectl exec deployment/postgres -n twisterlab -- pg_dump -U twisterlab twisterlab > backup_$(date +%Y%m%d).sql

# Restore backup
kubectl exec -i deployment/postgres -n twisterlab -- psql -U twisterlab twisterlab < backup.sql

# Check database size
kubectl exec deployment/postgres -n twisterlab -- psql -U twisterlab -c "\l+"
```

## Agent Development Guidelines

### Agent Lifecycle
1. **Design**: Define agent purpose, inputs, outputs
2. **Scaffold**: Use `scripts/new_agent_scaffold.py`
3. **Implement**: Extend `TwisterAgent`, implement `execute()` method
4. **Test**: Write unit tests with mocked dependencies
5. **Register**: Add to `AgentRegistry.initialize_agents()`
6. **Deploy**: Create K8s manifest if needed
7. **Monitor**: Add custom metrics for agent-specific KPIs

### Agent Communication Pattern
```python
# agents/real/example_agent.py
from twisterlab.agents.base import TwisterAgent
from twisterlang.codec import build_message, validate_message

class ExampleAgent(TwisterAgent):
    async def execute(self, task: str, context: dict = None) -> dict:
        # 1. Validate input
        if not task:
            return {"error": "Task is required"}
        
        # 2. Build TwisterLang message
        message = build_message(
            tool_name="example_tool",
            args={"task": task, **context}
        )
        
        # 3. Execute business logic
        result = await self._process_task(task, context)
        
        # 4. Return structured response
        return {
            "status": "success",
            "correlation_id": message["correlation_id"],
            "result": result
        }
```

### Testing Agents
```python
# tests/test_agents/test_example_agent.py
import pytest
from twisterlab.agents.real.example_agent import ExampleAgent

@pytest.mark.asyncio
@pytest.mark.unit
async def test_example_agent_execute():
    agent = ExampleAgent()
    result = await agent.execute("test task", {"user": "test"})
    
    assert result["status"] == "success"
    assert "correlation_id" in result
    assert result["result"] is not None

@pytest.mark.asyncio
@pytest.mark.integration
async def test_example_agent_with_registry():
    from twisterlab.agents.registry import AgentRegistry
    
    registry = AgentRegistry()
    agent = registry.get_agent("example")
    
    assert agent is not None
    assert isinstance(agent, ExampleAgent)
```

## MCP Tool Development

### Adding a New MCP Tool
1. **Define in MCP Server**: Add tool definition to `src/twisterlab/agents/mcp/mcp_server.py`
2. **Create API Route**: Add endpoint to `src/twisterlab/api/routes_mcp_real.py`
3. **Wire to Agent**: Call appropriate agent's `execute()` method
4. **Document**: Add to API docs and tool registry

### Example MCP Tool Route
```python
# src/twisterlab/api/routes_mcp_real.py
@router.post("/my_custom_tool", response_model=MCPResponse)
async def my_custom_tool(request: MCPToolRequest):
    """
    Custom MCP tool for specific functionality.
    
    TwisterLang Protocol:
    - tool_name: "my_custom_tool"
    - args: {"param1": "value1", "param2": "value2"}
    """
    try:
        # Get agent from registry
        registry = AgentRegistry()
        agent = registry.get_agent("custom-agent")
        
        # Extract parameters from TwisterLang message
        args = request.message.get("payload", {}).get("args", {})
        
        # Execute agent task
        result = await agent.execute(
            task=args.get("param1"),
            context=args
        )
        
        # Return MCP-compliant response
        return MCPResponse(
            content=[{"type": "text", "text": str(result)}],
            isError=False
        )
    except Exception as e:
        logger.exception(f"Error in my_custom_tool: {e}")
        return MCPResponse(
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            isError=True
        )
```

## Useful Makefile Targets
```powershell
# View all available targets
make help

# Install dependencies
make install

# Run tests with coverage
make test

# Lint and format code
make lint
make format

# Build Docker images
make build

# Start local dev environment
make dev

# Deploy to Kubernetes
make deploy

# View logs
make logs
```
