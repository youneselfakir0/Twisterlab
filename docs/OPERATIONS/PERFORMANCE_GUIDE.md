# TwisterLab Performance Optimization Guide

## 🎯 Performance Targets (SLOs)

### API Performance
- **p50 latency**: < 100ms
- **p95 latency**: < 500ms
- **p99 latency**: < 1000ms
- **Error rate**: < 0.5%
- **Availability**: 99.9% (43 minutes downtime/month)

### Agent Performance
- **Agent execution time**: < 30s per task
- **Agent success rate**: > 98%
- **Concurrent agent tasks**: > 100

### Database Performance
- **Query time p95**: < 50ms
- **Connection pool utilization**: < 80%
- **Transaction throughput**: > 1000 TPS

---

## 📊 Performance Monitoring

### Real-Time Monitoring Dashboard

Access Grafana dashboards:
- **System Overview**: `http://grafana.twisterlab.local/d/system-overview`
- **API Performance**: `http://grafana.twisterlab.local/d/api-perf`
- **Database Performance**: `http://grafana.twisterlab.local/d/db-perf`

### Key Metrics to Watch

```promql
# API Request Rate
rate(http_requests_total[5m])

# API Latency (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error Rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Agent Execution Time
histogram_quantile(0.95, rate(twisterlab_agent_execution_seconds_bucket[5m]))

# Database Connection Pool
pg_stat_database_numbackends / pg_settings_max_connections

# Memory Usage
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100
```

---

## 🚀 API Optimization

### 1. Enable Response Caching

**Problem**: Repeated identical requests hitting database

**Solution**: Implement Redis caching for read-heavy endpoints

```python
# src/twisterlab/api/routes/agents.py
from functools import lru_cache
from fastapi_cache.decorator import cache
import aioredis

@router.get("/{agent_id}", response_model=AgentResponse)
@cache(expire=300)  # Cache for 5 minutes
async def get_agent(agent_id: str, tenantId: str | None = None, 
                   repo: AgentRepo = Depends(get_agent_repo)):
    agent_obj = await repo.get_agent(agent_id, partition_key=tenantId)
    if not agent_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_obj
```

**Configuration**:
```python
# src/twisterlab/api/main.py
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import aioredis

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        encoding="utf8",
        decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="twisterlab-cache")
```

**Expected Impact**: 50-70% reduction in database load, 80% faster response time for cached data

---

### 2. Database Connection Pooling Optimization

**Problem**: Connection exhaustion under high load

**Current**:
```python
# src/twisterlab/database/session.py
engine = create_async_engine(DATABASE_URL)  # Default: 5 connections
```

**Optimized**:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,              # Increase from 5
    max_overflow=10,           # Allow 10 extra connections
    pool_pre_ping=True,        # Verify connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo_pool="debug",         # Log pool activity (dev only)
    connect_args={
        "server_settings": {
            "application_name": "twisterlab-api",
            "jit": "off"       # Disable JIT for faster simple queries
        }
    }
)
```

**Expected Impact**: Handle 3x more concurrent requests, eliminate connection timeouts

---

### 3. Async Batch Operations

**Problem**: N+1 query pattern when fetching related data

**Bad**:
```python
# Fetches agents, then makes N queries for tasks
agents = await session.execute(select(Agent))
for agent in agents.scalars():
    tasks = await session.execute(
        select(Task).where(Task.agent_id == agent.id)
    )
```

**Good**:
```python
# Single query with joined load
from sqlalchemy.orm import selectinload

agents = await session.execute(
    select(Agent).options(selectinload(Agent.tasks))
)
# Tasks are preloaded, no additional queries
```

**Expected Impact**: 90% reduction in query count, 70% faster for list operations

---

### 4. Request Compression

**Problem**: Large JSON responses consuming bandwidth

**Solution**: Enable Gzip compression in FastAPI

```python
# src/twisterlab/api/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB
```

**Expected Impact**: 60-80% smaller response sizes, faster for clients on slow networks

---

### 5. Rate Limiting

**Problem**: Resource exhaustion from excessive requests

**Solution**: Implement per-IP rate limiting using Custom Middleware.

```python
# src/twisterlab/agents/api/security.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    # Custom Token Bucket implementation
    pass

# src/twisterlab/api/main.py
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
```

**Expected Impact**: Prevent DDoS, ensure fair resource distribution

---

## 🗄️ Database Optimization

### 1. Add Missing Indexes

**Identify slow queries**:
```powershell
kubectl exec deployment/postgres -n twisterlab -- psql -U twisterlab -c "
  SELECT 
    query,
    calls,
    total_exec_time / 1000 as total_time_sec,
    mean_exec_time / 1000 as mean_time_sec
  FROM pg_stat_statements
  WHERE mean_exec_time > 100  -- Queries taking > 100ms
  ORDER BY total_exec_time DESC
  LIMIT 10;
"
```

**Create indexes for common patterns**:
```sql
-- Agent lookup by name
CREATE INDEX CONCURRENTLY idx_agent_name ON agents(name);

-- Agent lookup by tenant
CREATE INDEX CONCURRENTLY idx_agent_tenant ON agents(tenant_id);

-- Composite index for common query
CREATE INDEX CONCURRENTLY idx_agent_tenant_name ON agents(tenant_id, name);

-- Partial index for active agents only
CREATE INDEX CONCURRENTLY idx_agent_active 
  ON agents(tenant_id, status) 
  WHERE status = 'active';
```

**Alembic migration**:
```python
# alembic/versions/XXXX_add_performance_indexes.py
def upgrade():
    op.create_index(
        'idx_agent_name', 
        'agents', 
        ['name'], 
        unique=False,
        postgresql_concurrently=True  # No table lock during creation
    )
    op.create_index(
        'idx_agent_tenant', 
        'agents', 
        ['tenant_id'], 
        unique=False,
        postgresql_concurrently=True
    )
```

**Expected Impact**: 10x faster lookup queries, enable query optimizer

---

### 2. Query Optimization

**Enable query logging**:
```sql
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 100;  -- Log queries > 100ms
SELECT pg_reload_conf();
```

**Analyze query plans**:
```powershell
kubectl exec deployment/postgres -n twisterlab -- psql -U twisterlab -c "
  EXPLAIN ANALYZE 
  SELECT * FROM agents WHERE tenant_id = 'tenant-123' AND status = 'active';
"
```

**Optimize with CTEs and subqueries**:
```python
# Bad: Multiple round trips
agents = await session.execute(select(Agent).where(Agent.status == 'active'))
for agent in agents.scalars():
    count = await session.execute(
        select(func.count(Task.id)).where(Task.agent_id == agent.id)
    )

# Good: Single query with window function
stmt = select(
    Agent,
    func.count(Task.id).over(partition_by=Agent.id).label('task_count')
).join(Task, isouter=True).where(Agent.status == 'active')
result = await session.execute(stmt)
```

**Expected Impact**: 80% reduction in query time for complex operations

---

### 3. Connection Pooling with PgBouncer

**Problem**: High connection overhead from short-lived connections

**Solution**: Deploy PgBouncer between API and PostgreSQL

```yaml
# k8s/deployments/pgbouncer.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
  namespace: twisterlab
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: pgbouncer
        image: edoburu/pgbouncer:1.21
        env:
        - name: DATABASE_URL
          value: "postgres://twisterlab:pass@postgres:5432/twisterlab"
        - name: POOL_MODE
          value: "transaction"  # Best for stateless apps
        - name: MAX_CLIENT_CONN
          value: "1000"
        - name: DEFAULT_POOL_SIZE
          value: "25"
        ports:
        - containerPort: 5432
```

**Update API to use PgBouncer**:
```yaml
# k8s/base/secrets.yaml
DATABASE_URL: postgresql+asyncpg://twisterlab:pass@pgbouncer:5432/twisterlab
```

**Expected Impact**: Support 10x more concurrent connections, reduce connection overhead

---

### 4. Vacuum and Analyze Automation

**Problem**: Table bloat and stale statistics causing slow queries

**Solution**: Automate maintenance with CronJob

```yaml
# k8s/deployments/postgres-maintenance.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-vacuum
  namespace: twisterlab
spec:
  schedule: "0 2 * * 0"  # Every Sunday at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: vacuum
            image: postgres:16
            command:
            - /bin/sh
            - -c
            - |
              psql -U twisterlab -d twisterlab -c "VACUUM ANALYZE;"
            env:
            - name: PGHOST
              value: postgres
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
          restartPolicy: OnFailure
```

**Expected Impact**: Maintain query performance over time, prevent bloat

---

## 🧠 Agent Optimization

### 1. Agent Execution Caching

**Problem**: Identical agent tasks executing repeatedly

**Solution**: Cache agent results with TTL

```python
# src/twisterlab/agents/base.py
import hashlib
import json
from functools import wraps

def cache_agent_result(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, task: str, context: dict = None):
            # Create cache key from task and context
            cache_key = hashlib.md5(
                json.dumps({"task": task, "context": context}, sort_keys=True).encode()
            ).hexdigest()
            
            # Check cache
            cached = await redis_client.get(f"agent:{self.name}:{cache_key}")
            if cached:
                return json.loads(cached)
            
            # Execute and cache
            result = await func(self, task, context)
            await redis_client.setex(
                f"agent:{self.name}:{cache_key}",
                ttl,
                json.dumps(result)
            )
            return result
        return wrapper
    return decorator

class CoreAgent:
    @cache_agent_result(ttl=600)  # Cache for 10 minutes
    async def execute(self, task: str, context: dict = None):
        # Agent execution logic
        pass
```

**Expected Impact**: 90% faster for duplicate requests, reduce LLM API costs

---

### 2. Parallel Agent Execution

**Problem**: Sequential agent calls increasing total time

**Solution**: Execute independent agents in parallel

```python
# src/twisterlab/agents/real/real_maestro_agent.py
import asyncio

async def orchestrate_parallel(self, tasks: list):
    # Bad: Sequential execution (30s total for 3x 10s tasks)
    # results = []
    # for task in tasks:
    #     result = await agent.execute(task)
    #     results.append(result)
    
    # Good: Parallel execution (10s total)
    agent_coroutines = [
        self.registry.get_agent(task['agent']).execute(task['input'])
        for task in tasks
    ]
    results = await asyncio.gather(*agent_coroutines, return_exceptions=True)
    return results
```

**Expected Impact**: 3x faster for orchestrated workflows

---

### 3. Agent Circuit Breaker

**Problem**: Slow/failing agent blocking entire system

**Solution**: Implement circuit breaker pattern

```python
# src/twisterlab/agents/base.py
from circuitbreaker import circuit

class TwisterAgent:
    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=Exception)
    async def execute(self, task: str, context: dict = None):
        # If agent fails 5 times, circuit opens for 60 seconds
        # Prevents cascading failures
        pass
```

**Expected Impact**: Graceful degradation, prevent cascade failures

---

## 🐳 Container Optimization

### 1. Multi-Stage Docker Build

**Problem**: Large image size (1.2GB) causing slow deployments

**Optimized Dockerfile**:
```dockerfile
# Dockerfile.api (optimized)
# Stage 1: Build
FROM python:3.12-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-alpine  # Alpine base = 50MB vs 200MB
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "twisterlab.api.main:app", "--host", "0.0.0.0"]
```

**Expected Impact**: Image size reduced from 1.2GB → 250MB, 5x faster deployments

---

### 2. Resource Limits Tuning

**Problem**: Pods being OOM killed or CPU throttled

**Optimized deployment**:
```yaml
# k8s/deployments/twisterlab-api.yaml
resources:
  requests:
    memory: "512Mi"    # Guaranteed minimum
    cpu: "500m"        # 0.5 CPU cores
  limits:
    memory: "1Gi"      # Max before OOM kill
    cpu: "2000m"       # Max CPU (2 cores)
```

**Monitor and adjust**:
```powershell
# Check actual usage
kubectl top pod -n twisterlab

# Adjust if usage consistently near limits
kubectl set resources deployment/twisterlab-api -n twisterlab \
  --requests=cpu=1,memory=1Gi \
  --limits=cpu=3,memory=2Gi
```

**Expected Impact**: Optimal resource utilization, prevent OOM/throttling

---

## 📈 Load Testing & Benchmarking

### Load Testing with k6

**Create load test script**:
```javascript
// tests/load/full-workflow.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],  // 95% < 500ms
    http_req_failed: ['rate<0.01'],                   // Error rate < 1%
  },
};

export default function () {
  // Test health endpoint
  let health = http.get('http://edgeserver.twisterlab.local:30001/health');
  check(health, { 'health check passed': (r) => r.status === 200 });
  
  // Test MCP tool
  let classify = http.post(
    'http://edgeserver.twisterlab.local:30001/mcp/classify_ticket',
    JSON.stringify({
      message: { payload: { args: { ticket: 'test ticket' } } }
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(classify, { 'classify succeeded': (r) => r.status === 200 });
  
  sleep(1);
}
```

**Run load test**:
```powershell
k6 run tests/load/full-workflow.js --out json=load-test-results.json

# Generate HTML report
docker run --rm -v ${PWD}:/app -w /app \
  loadimpact/k6report load-test-results.json -o report.html
```

**Expected Results**:
- 100 concurrent users
- p95 latency < 500ms
- 0% error rate
- Throughput > 1000 req/sec

---

## 🎛️ Performance Tuning Checklist

### Before Optimization
- [ ] Establish baseline metrics
- [ ] Identify bottlenecks with profiling
- [ ] Set specific performance targets

### During Optimization
- [ ] Change one variable at a time
- [ ] Measure impact of each change
- [ ] Document configuration changes

### After Optimization
- [ ] Verify improvements in production
- [ ] Update documentation
- [ ] Set up alerts for regressions

---

## 🔍 Performance Debugging Tools

### Python Profiling

```powershell
# Profile API endpoint
python -m cProfile -o api.prof -m uvicorn twisterlab.api.main:app

# Analyze with snakeviz
pip install snakeviz
snakeviz api.prof
```

### Database Query Analysis

```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries
SELECT 
  substring(query, 1, 100) as short_query,
  calls,
  total_exec_time::numeric(10,2) as total_time_ms,
  mean_exec_time::numeric(10,2) as mean_time_ms,
  stddev_exec_time::numeric(10,2) as stddev_time_ms
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

### Memory Profiling

```python
# Install memory_profiler
# pip install memory_profiler

from memory_profiler import profile

@profile
async def execute_heavy_task():
    # Your code here
    pass
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-10  
**Maintained By**: DevOps Team
