# TwisterLab Operations Runbook

## 🚨 Emergency Contacts & Escalation

### On-Call Rotation
- **Primary**: Check PagerDuty/Opsgenie
- **Secondary**: Escalate after 15 minutes
- **Manager**: Escalate for P0/P1 incidents

### Communication Channels
- **Slack**: `#twisterlab-incidents`
- **Status Page**: `status.twisterlab.local`
- **Incident Bridge**: Conference line in incident channel

---

## 📊 Health Check & Monitoring

### System Health Dashboard
```powershell
# Quick health check
curl http://edgeserver.twisterlab.local:30001/health | jq

# Expected output:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected",
#   "agents": "operational"
# }
```

### Key Metrics to Monitor
1. **API Latency**: p95 < 500ms, p99 < 1s
2. **Error Rate**: < 1% of requests
3. **Agent Success Rate**: > 95%
4. **Database Connections**: < 80% of pool size
5. **Memory Usage**: < 80% of limit

### Grafana Dashboards
- **System Overview**: http://grafana.twisterlab.local/d/system-overview
- **Agent Performance**: http://grafana.twisterlab.local/d/agent-perf
- **Database Metrics**: http://grafana.twisterlab.local/d/database

---

## 🔥 Common Incidents & Resolution

### Incident 1: API Pods Crashing (CrashLoopBackOff)

**Symptoms:**
- API endpoints returning 502/503
- Pods in CrashLoopBackOff state
- Health check failing

**Diagnosis:**
```powershell
# Check pod status
kubectl get pods -n twisterlab | grep twisterlab-api

# Check recent logs
kubectl logs deployment/twisterlab-api -n twisterlab --tail=100

# Check events
kubectl describe pod <pod-name> -n twisterlab
```

**Common Causes & Fixes:**

1. **Database connection failure**
   ```powershell
   # Verify DATABASE_URL secret
   kubectl get secret twisterlab-secrets -n twisterlab -o jsonpath='{.data.DATABASE_URL}' | base64 -d
   
   # Test database connectivity
   kubectl exec -it deployment/postgres -n twisterlab -- pg_isready
   
   # Fix: Update secret if wrong
   kubectl delete secret twisterlab-secrets -n twisterlab
   kubectl create secret generic twisterlab-secrets \
     --from-literal=DATABASE_URL='postgresql+asyncpg://user:pass@postgres:5432/twisterlab' \
     -n twisterlab
   kubectl rollout restart deployment/twisterlab-api -n twisterlab
   ```

2. **OOM (Out of Memory)**
   ```powershell
   # Check memory usage
   kubectl top pod -n twisterlab | grep twisterlab-api
   
   # Fix: Increase memory limits
   kubectl set resources deployment/twisterlab-api -n twisterlab \
     --limits=memory=2Gi --requests=memory=1Gi
   ```

3. **Missing environment variables**
   ```powershell
   # Check env vars
   kubectl exec deployment/twisterlab-api -n twisterlab -- env | grep -E "DATABASE|REDIS|API"
   
   # Fix: Update ConfigMap or Secret
   kubectl edit configmap twisterlab-config -n twisterlab
   kubectl rollout restart deployment/twisterlab-api -n twisterlab
   ```

**Prevention:**
- Set proper resource limits and requests
- Add startup probes with longer initialDelaySeconds
- Implement circuit breakers for external dependencies

---

### Incident 2: High API Latency

**Symptoms:**
- API response time > 2s
- Timeout errors
- Queue backlog increasing

**Diagnosis:**
```powershell
# Check current latency
curl -w "@curl-format.txt" -o /dev/null -s http://edgeserver.twisterlab.local:30001/health

# Check Prometheus metrics
curl http://edgeserver.twisterlab.local:30001/metrics | grep http_request_duration

# Check database slow queries
kubectl exec deployment/postgres -n twisterlab -- psql -U twisterlab -c \
  "SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
   FROM pg_stat_activity 
   WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';"
```

**Common Causes & Fixes:**

1. **Database connection pool exhausted**
   ```python
   # src/twisterlab/database/session.py
   # Increase pool size
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,      # Increase from 5
       max_overflow=10    # Increase from 10
   )
   ```

2. **N+1 query problem**
   ```python
   # Bad: N+1 queries
   for agent in agents:
       tasks = await get_tasks(agent.id)  # Query per agent
   
   # Good: Single query with join
   agents_with_tasks = await session.execute(
       select(Agent).options(selectinload(Agent.tasks))
   )
   ```

3. **Missing database indexes**
   ```powershell
   # Create Alembic migration
   alembic revision -m "add_indexes_for_common_queries"
   
   # In migration file:
   # op.create_index('ix_agent_name', 'agents', ['name'])
   # op.create_index('ix_agent_tenant', 'agents', ['tenant_id'])
   
   alembic upgrade head
   ```

4. **Redis cache miss**
   ```powershell
   # Check Redis connectivity
   kubectl exec deployment/redis -n twisterlab -- redis-cli ping
   
   # Check hit rate
   kubectl exec deployment/redis -n twisterlab -- redis-cli INFO stats | grep hit
   
   # Warm up cache
   curl -X POST http://edgeserver.twisterlab.local:30001/admin/cache/warm
   ```

**Prevention:**
- Add database query monitoring
- Set query timeout limits
- Implement proper caching strategy
- Add indexes for frequently queried columns

---

### Incident 3: MCP Tools Not Responding

**Symptoms:**
- Continue IDE/Claude Desktop can't access tools
- "Tool not found" errors
- MCP server shows HYBRID mode instead of REAL

**Diagnosis:**
```powershell
# Check MCP server logs
kubectl logs deployment/mcp-unified -n twisterlab --tail=100

# Test API connectivity from MCP pod
kubectl exec deployment/mcp-unified -n twisterlab -- curl http://twisterlab-api:8000/health

# Verify API_URL environment variable
kubectl exec deployment/mcp-unified -n twisterlab -- env | grep API_URL
```

**Common Causes & Fixes:**

1. **API not reachable from MCP pod**
   ```powershell
   # Check service exists
   kubectl get svc twisterlab-api -n twisterlab
   
   # Test DNS resolution
   kubectl exec deployment/mcp-unified -n twisterlab -- nslookup twisterlab-api
   
   # Fix: Update API_URL to use service name
   kubectl set env deployment/mcp-unified API_URL=http://twisterlab-api:8000 -n twisterlab
   ```

2. **Network policy blocking traffic**
   ```powershell
   # Check network policies
   kubectl get networkpolicies -n twisterlab
   
   # Temporarily allow all (for testing only!)
   kubectl delete networkpolicy --all -n twisterlab
   
   # Fix: Create proper network policy
   kubectl apply -f k8s/base/network-policy.yaml
   ```

3. **MCP server in wrong mode**
   ```powershell
   # Force REAL mode
   kubectl set env deployment/mcp-unified MCP_MODE=REAL -n twisterlab
   kubectl rollout restart deployment/mcp-unified -n twisterlab
   ```

**Prevention:**
- Add MCP → API connectivity health check
- Monitor MCP tool success rate
- Alert on mode switches (REAL → HYBRID)

---

### Incident 4: Database Connection Exhaustion

**Symptoms:**
- "Too many connections" errors
- API requests timing out
- PostgreSQL max_connections reached

**Diagnosis:**
```powershell
# Check current connections
kubectl exec deployment/postgres -n twisterlab -- psql -U twisterlab -c \
  "SELECT count(*) as connections, state FROM pg_stat_activity GROUP BY state;"

# Check max connections limit
kubectl exec deployment/postgres -n twisterlab -- psql -U twisterlab -c "SHOW max_connections;"

# Find connection leaks
kubectl exec deployment/postgres -n twisterlab -- psql -U twisterlab -c \
  "SELECT pid, usename, application_name, client_addr, state, 
          backend_start, state_change 
   FROM pg_stat_activity 
   WHERE state = 'idle' 
   AND state_change < now() - interval '10 minutes';"
```

**Fixes:**

1. **Increase PostgreSQL max_connections**
   ```powershell
   # Edit postgres ConfigMap
   kubectl edit configmap postgres-config -n twisterlab
   # Add: max_connections = 200
   
   # Restart postgres
   kubectl rollout restart deployment/postgres -n twisterlab
   ```

2. **Fix connection leaks in code**
   ```python
   # Always use context managers
   async def get_agents():
       async with AsyncSessionLocal() as session:
           result = await session.execute(select(Agent))
           return result.scalars().all()
       # Session automatically closed here
   ```

3. **Scale API pods**
   ```powershell
   # Reduce connections per pod
   kubectl scale deployment/twisterlab-api --replicas=5 -n twisterlab
   ```

**Prevention:**
- Set aggressive connection timeouts
- Monitor connection pool usage
- Use connection pooling (PgBouncer)

---

### Incident 5: Agent Execution Failures

**Symptoms:**
- Agent tasks timing out
- "Agent not found" errors
- Inconsistent agent responses

**Diagnosis:**
```powershell
# Check agent registry
curl http://edgeserver.twisterlab.local:30001/mcp/list_autonomous_agents

# Test specific agent
curl -X POST http://edgeserver.twisterlab.local:30001/mcp/classify_ticket \
  -H "Content-Type: application/json" \
  -d '{"message": {"payload": {"args": {"ticket": "test"}}}}'

# Check agent logs
kubectl logs deployment/twisterlab-api -n twisterlab | grep -i "agent"
```

**Common Causes & Fixes:**

1. **Agent not registered**
   ```python
   # src/twisterlab/agents/registry.py
   def initialize_agents(self):
       # Ensure agent is added here
       my_agent = MyCustomAgent()
       self._agents[my_agent.name.lower()] = my_agent
   ```

2. **Agent LLM backend unreachable**
   ```powershell
   # Check Ollama/LLM service
   curl http://ollama-service:11434/api/tags
   
   # Test from API pod
   kubectl exec deployment/twisterlab-api -n twisterlab -- \
     curl http://ollama-service:11434/api/tags
   ```

3. **Agent timeout too short**
   ```python
   # Increase timeout in agent execution
   async def execute(self, task, context=None):
       async with asyncio.timeout(300):  # 5 minutes
           return await self._process(task, context)
   ```

**Prevention:**
- Add agent health checks
- Monitor agent execution time
- Implement retry logic with exponential backoff

---

## 🔧 Maintenance Procedures

### Planned Maintenance Window

**Pre-Maintenance Checklist:**
- [ ] Announce maintenance 48 hours in advance
- [ ] Update status page
- [ ] Backup database
- [ ] Test rollback procedure
- [ ] Prepare rollback plan

**Maintenance Steps:**
```powershell
# 1. Put system in maintenance mode
kubectl scale deployment/twisterlab-api --replicas=0 -n twisterlab

# 2. Backup database
kubectl exec deployment/postgres -n twisterlab -- \
  pg_dump -U twisterlab twisterlab > maintenance_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Apply changes (migrations, config updates, etc.)
alembic upgrade head

# 4. Deploy new version
kubectl set image deployment/twisterlab-api twisterlab-api=twisterlab-api:v2.0 -n twisterlab

# 5. Scale back up
kubectl scale deployment/twisterlab-api --replicas=3 -n twisterlab

# 6. Verify health
kubectl rollout status deployment/twisterlab-api -n twisterlab
curl http://edgeserver.twisterlab.local:30001/health

# 7. Exit maintenance mode
kubectl annotate deployment/twisterlab-api maintenance=complete -n twisterlab
```

### Database Vacuum & Analyze

**When to run:**
- Weekly during low-traffic hours
- After large data imports/deletes

```powershell
# Full vacuum (requires downtime)
kubectl exec deployment/postgres -n twisterlab -- \
  psql -U twisterlab -c "VACUUM FULL ANALYZE;"

# Online vacuum (no downtime)
kubectl exec deployment/postgres -n twisterlab -- \
  psql -U twisterlab -c "VACUUM ANALYZE;"

# Check table bloat
kubectl exec deployment/postgres -n twisterlab -- \
  psql -U twisterlab -c "
    SELECT schemaname, tablename, 
           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
    FROM pg_tables 
    WHERE schemaname = 'public' 
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Log Rotation & Cleanup

```powershell
# Clean old logs (keep last 7 days)
kubectl delete pod -n twisterlab \
  --field-selector=status.phase==Succeeded,status.phase==Failed \
  --selector=job-name

# Archive logs to S3
kubectl logs deployment/twisterlab-api -n twisterlab --since=24h > logs_$(date +%Y%m%d).txt
aws s3 cp logs_$(date +%Y%m%d).txt s3://twisterlab-logs/

# Prune old Docker images on nodes
kubectl debug node/worker-node -it --image=alpine -- sh
# docker image prune -a --filter "until=168h"
```

---

## 📈 Capacity Planning

### Resource Monitoring
```powershell
# Check resource usage trends
kubectl top nodes
kubectl top pods -n twisterlab --sort-by=memory

# Prometheus queries for capacity planning
# CPU usage trend (7 days):
# rate(container_cpu_usage_seconds_total{namespace="twisterlab"}[7d])

# Memory usage trend (7 days):
# container_memory_usage_bytes{namespace="twisterlab"}
```

### Scaling Guidelines

**When to scale up:**
- CPU usage > 70% sustained for 10+ minutes
- Memory usage > 80%
- Request queue depth > 100
- p95 latency > 1s

**Horizontal Scaling:**
```powershell
# API pods
kubectl scale deployment/twisterlab-api --replicas=5 -n twisterlab

# Configure HPA (auto-scaling)
kubectl autoscale deployment/twisterlab-api \
  --cpu-percent=70 \
  --min=2 --max=10 \
  -n twisterlab
```

**Vertical Scaling:**
```powershell
# Increase resources
kubectl set resources deployment/twisterlab-api -n twisterlab \
  --limits=cpu=2,memory=2Gi \
  --requests=cpu=1,memory=1Gi
```

---

## 🔐 Security Incident Response

### Suspected Security Breach

**Immediate Actions:**
1. **Isolate affected systems**
   ```powershell
   # Remove from load balancer
   kubectl scale deployment/twisterlab-api --replicas=0 -n twisterlab
   
   # Block ingress traffic
   kubectl delete ingress twisterlab-ingress -n twisterlab
   ```

2. **Preserve evidence**
   ```powershell
   # Snapshot all logs
   kubectl logs deployment/twisterlab-api -n twisterlab --all-containers=true > incident_logs.txt
   
   # Snapshot database
   kubectl exec deployment/postgres -n twisterlab -- \
     pg_dump -U twisterlab twisterlab > incident_db_snapshot.sql
   ```

3. **Rotate all secrets**
   ```powershell
   # Generate new secrets
   kubectl delete secret twisterlab-secrets -n twisterlab
   kubectl create secret generic twisterlab-secrets \
     --from-literal=DATABASE_URL='<new-connection-string>' \
     --from-literal=REDIS_URL='<new-redis-url>' \
     -n twisterlab
   ```

4. **Notify stakeholders**
   - Security team
   - Management
   - Customers (if data breach)

---

## 📞 Support Escalation Matrix

| Severity | Response Time | Escalation |
|----------|--------------|------------|
| P0 (System Down) | 5 minutes | Immediately to Manager |
| P1 (Critical Feature) | 15 minutes | After 30 minutes |
| P2 (Major) | 1 hour | After 2 hours |
| P3 (Minor) | 4 hours | Next business day |

---

## 🎓 Training Resources

- **Architecture Overview**: `docs/architecture/README.md`
- **API Documentation**: `docs/API.md`
- **Copilot Instructions**: `.github/copilot-instructions.md`
- **Migration Guide**: `docs/MIGRATION_SWARM_K8S.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-10  
**Maintained By**: DevOps Team
