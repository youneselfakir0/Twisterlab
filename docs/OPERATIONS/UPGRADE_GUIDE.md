# TwisterLab Upgrade & Migration Guide

## Version Compatibility Matrix

| Component | Current | Min Required | Recommended |
|-----------|---------|--------------|-------------|
| Python | 3.11+ | 3.11 | 3.12 |
| PostgreSQL | 15+ | 13 | 16 |
| Kubernetes | 1.28+ | 1.25 | 1.29 |
| Redis | 7.0+ | 6.2 | 7.2 |
| Docker | 24.0+ | 20.10 | 25.0 |

---

## 🚀 Upgrade Strategies

### Zero-Downtime Deployment (Blue-Green)

**Use Case**: Production upgrades with zero downtime

**Steps**:
```powershell
# 1. Deploy new version alongside existing (green deployment)
kubectl apply -f k8s/deployments/twisterlab-api-v2.yaml -n twisterlab

# 2. Wait for new pods to be healthy
kubectl wait --for=condition=ready pod -l version=v2,app=twisterlab-api -n twisterlab --timeout=5m

# 3. Test new version with subset of traffic (canary)
kubectl patch svc twisterlab-api -n twisterlab -p '{"spec":{"selector":{"version":"v2"}}}'

# 4. Monitor metrics for 5-10 minutes
# Check Grafana dashboards for errors/latency

# 5. If successful, switch all traffic
kubectl scale deployment/twisterlab-api-v1 --replicas=0 -n twisterlab

# 6. Cleanup old deployment after verification period
kubectl delete deployment/twisterlab-api-v1 -n twisterlab
```

**Rollback**:
```powershell
# Immediately revert traffic to v1
kubectl patch svc twisterlab-api -n twisterlab -p '{"spec":{"selector":{"version":"v1"}}}'
kubectl scale deployment/twisterlab-api-v1 --replicas=3 -n twisterlab
```

---

### Rolling Update (Default Strategy)

**Use Case**: Standard upgrades with brief traffic interruption

**Steps**:
```powershell
# 1. Backup database
.\scripts\devops-toolkit.ps1 -Action backup -Environment production

# 2. Apply database migrations (if any)
kubectl exec deployment/twisterlab-api -n twisterlab -- alembic upgrade head

# 3. Update container image
kubectl set image deployment/twisterlab-api twisterlab-api=twisterlab-api:v2.0 -n twisterlab

# 4. Monitor rollout
kubectl rollout status deployment/twisterlab-api -n twisterlab

# 5. Verify health
.\scripts\devops-toolkit.ps1 -Action health -Environment production
```

**Rollback**:
```powershell
kubectl rollout undo deployment/twisterlab-api -n twisterlab
```

---

### Maintenance Window Upgrade

**Use Case**: Major version upgrades requiring downtime

**Pre-Upgrade Checklist**:
- [ ] Announce maintenance window 48+ hours in advance
- [ ] Create full database backup
- [ ] Test upgrade in staging environment
- [ ] Document rollback procedure
- [ ] Notify users via status page

**Steps**:
```powershell
# 1. Put system in maintenance mode (503 response)
kubectl scale deployment/twisterlab-api --replicas=0 -n twisterlab
kubectl apply -f k8s/maintenance-page.yaml -n twisterlab

# 2. Backup database
kubectl exec deployment/postgres -n twisterlab -- \
  pg_dump -U twisterlab -Fc twisterlab > backup_pre_upgrade_$(date +%Y%m%d).dump

# 3. Apply schema migrations
kubectl exec deployment/postgres -n twisterlab -- \
  psql -U twisterlab -d twisterlab < migrations/upgrade_v2.sql

# 4. Deploy new version
kubectl apply -f k8s/deployments/twisterlab-api-v2.yaml -n twisterlab

# 5. Run data migration scripts (if needed)
kubectl exec deployment/twisterlab-api -n twisterlab -- \
  python scripts/migrate_data_v2.py

# 6. Verify data integrity
kubectl exec deployment/twisterlab-api -n twisterlab -- \
  python scripts/verify_data_integrity.py

# 7. Scale up and exit maintenance mode
kubectl scale deployment/twisterlab-api --replicas=3 -n twisterlab
kubectl delete -f k8s/maintenance-page.yaml -n twisterlab

# 8. Monitor for issues
.\scripts\devops-toolkit.ps1 -Action health -Environment production
```

---

## 📦 Component-Specific Upgrades

### PostgreSQL Major Version Upgrade (13 → 16)

**Critical**: PostgreSQL major version upgrades require `pg_dump` and `pg_restore`

```powershell
# 1. Backup current database
kubectl exec deployment/postgres-13 -n twisterlab -- \
  pg_dump -U twisterlab -Fc twisterlab > backup_pg13_full.dump

# 2. Deploy PostgreSQL 16 (new deployment)
kubectl apply -f k8s/deployments/postgres-16.yaml -n twisterlab

# 3. Restore data to new PostgreSQL
kubectl exec deployment/postgres-16 -n twisterlab -- \
  pg_restore -U twisterlab -d twisterlab < backup_pg13_full.dump

# 4. Update DATABASE_URL secret
kubectl patch secret twisterlab-secrets -n twisterlab \
  -p '{"data":{"DATABASE_URL":"'$(echo "postgresql+asyncpg://twisterlab:pass@postgres-16:5432/twisterlab" | base64)'"}}}'

# 5. Restart API pods to pick up new DATABASE_URL
kubectl rollout restart deployment/twisterlab-api -n twisterlab

# 6. Verify connectivity
.\scripts\devops-toolkit.ps1 -Action debug -Environment production

# 7. After verification, delete old PostgreSQL
kubectl delete deployment/postgres-13 -n twisterlab
kubectl delete pvc postgres-13-data -n twisterlab
```

---

### Redis Upgrade (6.2 → 7.2)

**Note**: Redis 7.x is backward compatible with 6.x

```powershell
# 1. Flush cache (if acceptable) or create backup
kubectl exec deployment/redis -n twisterlab -- redis-cli SAVE
kubectl exec deployment/redis -n twisterlab -- cp /data/dump.rdb /backup/dump_$(date +%Y%m%d).rdb

# 2. Update image version
kubectl set image deployment/redis redis=redis:7.2-alpine -n twisterlab

# 3. Monitor rollout
kubectl rollout status deployment/redis -n twisterlab

# 4. Test connectivity
kubectl exec deployment/redis -n twisterlab -- redis-cli PING
```

---

### Kubernetes Cluster Upgrade (1.28 → 1.29)

**Pre-requisites**:
- Read [Kubernetes version skew policy](https://kubernetes.io/releases/version-skew-policy/)
- Upgrade control plane first, then worker nodes

```powershell
# 1. Check current version
kubectl version --short

# 2. Drain worker nodes one by one
kubectl drain worker-node-1 --ignore-daemonsets --delete-emptydir-data

# 3. Upgrade kubelet and kubectl on node (SSH to node)
# apt-get update && apt-get install -y kubelet=1.29.0-00 kubectl=1.29.0-00

# 4. Uncordon node
kubectl uncordon worker-node-1

# 5. Verify node version
kubectl get nodes -o wide

# 6. Repeat for all nodes

# 7. Update API deprecations (if any)
kubectl apply -f k8s/ --dry-run=server
```

---

## 🔄 Migration Scenarios

### Migrate from Docker Compose to Kubernetes

**Current State**: Running on Docker Compose  
**Target State**: Running on Kubernetes cluster

**Migration Steps**:

1. **Prepare Kubernetes manifests** (already in `k8s/`)
   
2. **Export data from Docker Compose**:
   ```powershell
   # Export PostgreSQL data
   docker exec twisterlab-db pg_dump -U twisterlab twisterlab > compose_export.sql
   
   # Export Redis data (optional)
   docker exec twisterlab-redis redis-cli SAVE
   docker cp twisterlab-redis:/data/dump.rdb ./redis_backup.rdb
   ```

3. **Setup Kubernetes cluster**:
   ```powershell
   # Apply all K8s resources
   kubectl apply -f k8s/base/ -n twisterlab
   kubectl apply -f k8s/deployments/ -n twisterlab
   ```

4. **Import data to Kubernetes**:
   ```powershell
   # Wait for PostgreSQL to be ready
   kubectl wait --for=condition=ready pod -l app=postgres -n twisterlab --timeout=5m
   
   # Restore database
   kubectl exec -i deployment/postgres -n twisterlab -- \
     psql -U twisterlab twisterlab < compose_export.sql
   ```

5. **Update DNS/Ingress**:
   ```powershell
   # Point edgeserver.twisterlab.local to K8s Ingress
   # Update /etc/hosts or DNS records
   ```

6. **Switch traffic**:
   ```powershell
   # Stop Docker Compose services
   docker-compose down
   
   # Verify K8s services
   .\scripts\devops-toolkit.ps1 -Action health -Environment production
   ```

---

### Migrate from SQLite to PostgreSQL

**Use Case**: Moving from dev SQLite to production PostgreSQL

**Steps**:

1. **Export SQLite data**:
   ```powershell
   # Using SQLAlchemy script
   python scripts/export_sqlite_to_sql.py > sqlite_export.sql
   ```

2. **Setup PostgreSQL**:
   ```powershell
   kubectl apply -f k8s/deployments/postgres.yaml -n twisterlab
   ```

3. **Import data**:
   ```powershell
   # Import data to PostgreSQL
   kubectl exec -i deployment/postgres -n twisterlab -- \
     psql -U twisterlab twisterlab < sqlite_export.sql
   ```

4. **Update DATABASE_URL**:
   ```powershell
   kubectl patch secret twisterlab-secrets -n twisterlab \
     -p '{"data":{"DATABASE_URL":"'$(echo "postgresql+asyncpg://user:pass@postgres:5432/twisterlab" | base64)'"}}}'
   
   kubectl rollout restart deployment/twisterlab-api -n twisterlab
   ```

---

### Migrate from Single Tenant to Multi-Tenant

**Architecture Change**: Adding `tenant_id` to all tables

**Steps**:

1. **Create Alembic migration**:
   ```powershell
   alembic revision -m "add_tenant_id_to_all_tables"
   ```

2. **Update migration file**:
   ```python
   # alembic/versions/XXXX_add_tenant_id.py
   def upgrade():
       op.add_column('agents', sa.Column('tenant_id', sa.String(50), nullable=True))
       op.create_index('ix_agent_tenant', 'agents', ['tenant_id'])
       # Set default tenant for existing data
       op.execute("UPDATE agents SET tenant_id = 'default' WHERE tenant_id IS NULL")
       op.alter_column('agents', 'tenant_id', nullable=False)
   ```

3. **Apply migration**:
   ```powershell
   kubectl exec deployment/twisterlab-api -n twisterlab -- alembic upgrade head
   ```

4. **Update application code** (already done in codebase - partition_key pattern)

5. **Test multi-tenancy**:
   ```powershell
   # Create agent with tenant
   curl -X POST http://edgeserver.twisterlab.local:30001/agents/ \
     -H "Content-Type: application/json" \
     -d '{"name": "test-agent", "tenantId": "tenant-123"}'
   ```

---

## 🧪 Testing Upgrades

### Staging Environment Testing

**Always test upgrades in staging first!**

```powershell
# 1. Refresh staging data from production (anonymized)
kubectl exec deployment/postgres -n twisterlab -- \
  pg_dump -U twisterlab twisterlab | \
  kubectl exec -i deployment/postgres -n twisterlab-staging -- \
  psql -U twisterlab twisterlab

# 2. Perform upgrade in staging
.\scripts\devops-toolkit.ps1 -Action deploy -Environment staging

# 3. Run integration tests
pytest tests/integration/ -v --env=staging

# 4. Run load tests
k6 run tests/load/load-test.js --env STAGE=staging

# 5. Verify metrics
# Check Grafana dashboards for anomalies
```

---

## 📋 Post-Upgrade Verification

### Comprehensive Health Check Script

```powershell
# Run after every upgrade
.\scripts\devops-toolkit.ps1 -Action health -Environment production

# Additional verification
# 1. Test all MCP tools
curl -X POST http://edgeserver.twisterlab.local:30001/mcp/list_autonomous_agents
curl -X POST http://edgeserver.twisterlab.local:30001/mcp/classify_ticket \
  -H "Content-Type: application/json" \
  -d '{"message": {"payload": {"args": {"ticket": "test"}}}}'

# 2. Verify database schema version
kubectl exec deployment/twisterlab-api -n twisterlab -- alembic current

# 3. Check for error logs
kubectl logs deployment/twisterlab-api -n twisterlab --since=1h | grep -i error

# 4. Verify metrics collection
curl http://edgeserver.twisterlab.local:30001/metrics | grep twisterlab_agent

# 5. Test browser agent (if applicable)
curl -X POST http://edgeserver.twisterlab.local:30001/browser/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## 🔙 Rollback Procedures

### Quick Rollback (Last Deployment)

```powershell
# Rollback to previous version
kubectl rollout undo deployment/twisterlab-api -n twisterlab

# Monitor rollback
kubectl rollout status deployment/twisterlab-api -n twisterlab

# Or use devops toolkit
.\scripts\devops-toolkit.ps1 -Action rollback -Environment production
```

### Full Rollback with Database Restore

```powershell
# 1. Scale down API
kubectl scale deployment/twisterlab-api --replicas=0 -n twisterlab

# 2. Restore database from backup
kubectl exec -i deployment/postgres -n twisterlab -- \
  psql -U twisterlab twisterlab < backups/backup_pre_upgrade_20251210.sql

# 3. Deploy previous version
kubectl set image deployment/twisterlab-api twisterlab-api=twisterlab-api:v1.9 -n twisterlab

# 4. Scale up
kubectl scale deployment/twisterlab-api --replicas=3 -n twisterlab

# 5. Verify
.\scripts\devops-toolkit.ps1 -Action health -Environment production
```

---

## 📊 Upgrade Monitoring Checklist

Post-upgrade, monitor for 24-48 hours:

- [ ] **Error rate**: Should remain < 1%
- [ ] **Latency**: p95 < 500ms, p99 < 1s
- [ ] **Agent success rate**: > 95%
- [ ] **Database connections**: Stable, no leaks
- [ ] **Memory usage**: No memory leaks
- [ ] **CPU usage**: Within normal range
- [ ] **Disk usage**: Not growing abnormally
- [ ] **User reports**: No increase in support tickets

---

## 🆘 Emergency Rollback Decision Matrix

| Issue | Severity | Action |
|-------|----------|--------|
| Error rate > 5% | Critical | Immediate rollback |
| API latency > 5s | Critical | Immediate rollback |
| Database corruption | Critical | Stop, restore backup |
| Error rate 1-5% | High | Investigate, prepare rollback |
| Minor UI issues | Medium | Fix forward |
| Performance degradation < 20% | Low | Monitor, optimize |

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-10  
**Maintained By**: DevOps Team
