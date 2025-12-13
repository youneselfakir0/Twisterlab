# 🚀 Quick Start - TwisterLab Production Deployment

## Phase 3 Complete: Docker Compose Production Stack

### ✅ What's Deployed

**8 Production Services**:
1. **PostgreSQL 16** - Database with persistent storage
2. **Redis 7** - Cache with AOF persistence
3. **TwisterLab API** - Main application (8 agents)
4. **MCP Server** - Model Context Protocol integration
5. **Prometheus** - Metrics collection
6. **Grafana** - Monitoring dashboards
7. **NGINX** - Reverse proxy with rate limiting
8. **pgAdmin** - Database management (optional)

---

## 🎯 30-Second Deployment

```powershell
# 1. Setup environment
cp .env.production.example .env

# 2. Edit passwords (IMPORTANT!)
notepad .env

# 3. Start stack
docker-compose -f docker-compose.production.yml up -d

# 4. Check health
curl http://localhost/health
```

---

## 🔍 Verify Deployment

### Check All Services
```powershell
docker-compose -f docker-compose.production.yml ps
```

Expected output:
```
NAME                  STATUS   PORTS
twisterlab-api        Up       0.0.0.0:8000->8000/tcp
twisterlab-postgres   Up       0.0.0.0:5432->5432/tcp
twisterlab-redis      Up       0.0.0.0:6379->6379/tcp
twisterlab-mcp        Up       
twisterlab-prometheus Up       0.0.0.0:9090->9090/tcp
twisterlab-grafana    Up       0.0.0.0:3000->3000/tcp
twisterlab-nginx      Up       0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### Test API
```powershell
# Health check
curl http://localhost/health

# List all agents
curl http://localhost/v1/mcp/tools/list_autonomous_agents

# Test sentiment analyzer (Phase 2 agent!)
curl -X POST http://localhost/v1/mcp/tools/analyze_sentiment `
  -H "Content-Type: application/json" `
  -d '{"text": "This deployment is amazing!", "detailed": true}'
```

---

## 📊 Access Dashboards

### Grafana (Monitoring)
- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: (from .env `GRAFANA_PASSWORD`)
- **Dashboard**: "TwisterLab - System Overview"

### Prometheus (Metrics)
- **URL**: http://localhost:9090
- **Query Example**: `rate(http_requests_total[5m])`

### pgAdmin (Database)
- **URL**: http://localhost:5050
- **Email**: (from .env `PGADMIN_EMAIL`)
- **Password**: (from .env `PGADMIN_PASSWORD`)

---

## 🧪 Test All 8 MCP Tools

```powershell
# Set base URL
$apiUrl = "http://localhost/v1/mcp/tools"

# 1. List autonomous agents
curl "$apiUrl/list_autonomous_agents"

# 2. Classify ticket
curl -X POST "$apiUrl/classify_ticket" `
  -H "Content-Type: application/json" `
  -d '{"ticket_id": "TEST-123", "description": "Database connection error"}'

# 3. Resolve ticket
curl -X POST "$apiUrl/resolve_ticket" `
  -H "Content-Type: application/json" `
  -d '{"ticket_id": "TEST-123", "classification": "database"}'

# 4. Monitor system health
curl -X POST "$apiUrl/monitor_system_health" `
  -H "Content-Type: application/json" `
  -d '{"detailed": true}'

# 5. Create backup
curl -X POST "$apiUrl/create_backup"

# 6. Sync data
curl -X POST "$apiUrl/sync_data" `
  -H "Content-Type: application/json" `
  -d '{"source": "local", "destination": "backup"}'

# 7. Execute desktop command
curl -X POST "$apiUrl/execute_desktop_command" `
  -H "Content-Type: application/json" `
  -d '{"command": "echo Hello from TwisterLab"}'

# 8. Analyze sentiment (NEW - Phase 2!)
curl -X POST "$apiUrl/analyze_sentiment" `
  -H "Content-Type: application/json" `
  -d '{"text": "I absolutely love this product!", "detailed": true}'
```

---

## 🛠️ Common Operations

### View Logs
```powershell
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f api

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 api
```

### Restart Service
```powershell
docker-compose -f docker-compose.production.yml restart api
```

### Stop All
```powershell
docker-compose -f docker-compose.production.yml down
```

### Stop and Remove Data
```powershell
# WARNING: This deletes all data!
docker-compose -f docker-compose.production.yml down -v
```

---

## 🔐 Security Checklist

Before production:
- [ ] Changed `POSTGRES_PASSWORD` in .env
- [ ] Changed `REDIS_PASSWORD` in .env
- [ ] Changed `GRAFANA_PASSWORD` in .env
- [ ] Generated SSL certificates (see `DEPLOYMENT.md`)
- [ ] Configured firewall rules
- [ ] Enabled NGINX HTTPS

---

## 🎓 Phase 2 Success Recap

**SentimentAnalyzerAgent Delivered**:
- ✅ 262 lines of production code
- ✅ 14 passing tests (100% coverage)
- ✅ Interactive demo with 4 modes
- ✅ 1,661 lines of documentation
- ✅ Now deployed in production stack!

**Test the Phase 2 Agent**:
```powershell
# Basic sentiment analysis
curl -X POST http://localhost/v1/mcp/tools/analyze_sentiment `
  -H "Content-Type: application/json" `
  -d '{"text": "This is fantastic!"}'

# Detailed analysis with keywords
curl -X POST http://localhost/v1/mcp/tools/analyze_sentiment `
  -H "Content-Type: application/json" `
  -d '{"text": "The product quality is excellent but delivery was slow.", "detailed": true}'

# Multilingual support
curl -X POST http://localhost/v1/mcp/tools/analyze_sentiment `
  -H "Content-Type: application/json" `
  -d '{"text": "¡Este producto es increíble!", "detailed": true}'
```

---

## 📈 Next Steps

### Immediate
1. Run health checks
2. Test all 8 MCP tools
3. Review Grafana dashboards
4. Check Prometheus metrics

### Short-term
1. Configure SSL/TLS for HTTPS
2. Setup automated backups
3. Create custom Grafana dashboards
4. Load testing

### Long-term
1. Kubernetes deployment (when cluster access restored)
2. Multi-region deployment
3. Advanced monitoring alerts
4. Auto-scaling configuration

---

## 🆘 Troubleshooting

### API not starting
```powershell
# Check logs
docker-compose -f docker-compose.production.yml logs api

# Common issue: Database not ready
# Solution: Wait 30 seconds for health checks
```

### Cannot connect to database
```powershell
# Verify postgres is running
docker-compose -f docker-compose.production.yml ps postgres

# Test connection
docker-compose -f docker-compose.production.yml exec postgres psql -U twisterlab -c "SELECT version();"
```

### Port already in use
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Change ports in docker-compose.production.yml
```

---

## 📚 Documentation

- **Full Deployment Guide**: `DEPLOYMENT.md`
- **API Reference**: http://localhost/docs
- **Phase 2 Summary**: `PHASE2_COMPLETE.md`
- **Architecture**: `docs/architecture/`

---

**🎉 Congratulations! Your TwisterLab production stack is ready to deploy!**

For detailed instructions, see `DEPLOYMENT.md`.
