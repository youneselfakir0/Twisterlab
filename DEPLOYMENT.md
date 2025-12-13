# TwisterLab Production Deployment Guide

## 🚀 Quick Start (Docker Compose)

### Prerequisites
- Docker 20.10+ and Docker Compose v2+
- 4GB RAM minimum (8GB recommended)
- 10GB disk space

### 1. Setup Environment
```bash
# Clone repository
git clone https://github.com/youneselfakir0/twisterlab.git
cd twisterlab

# Create environment file
cp .env.production.example .env

# Edit .env and set secure passwords
# IMPORTANT: Change POSTGRES_PASSWORD, REDIS_PASSWORD, GRAFANA_PASSWORD
```

### 2. Pull Latest Images
```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/youneselfakir0/twisterlab/api:latest
docker pull ghcr.io/youneselfakir0/twisterlab/mcp:latest
```

### 3. Start Stack
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f api
```

### 4. Verify Deployment
```bash
# Check API health
curl http://localhost/health

# Test sentiment analysis
curl -X POST http://localhost/v1/mcp/tools/analyze_sentiment \
  -H "Content-Type: application/json" \
  -d '{"text": "This is excellent!", "detailed": true}'

# Access Grafana dashboard
# Open http://localhost:3000
# Login: admin / (password from .env)
```

---

## 📊 Services Overview

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **TwisterLab API** | 8000 | http://localhost/ | Main application |
| **Grafana** | 3000 | http://localhost:3000 | Metrics dashboard |
| **Prometheus** | 9090 | http://localhost:9090 | Metrics collection |
| **PostgreSQL** | 5432 | localhost:5432 | Database |
| **Redis** | 6379 | localhost:6379 | Cache |
| **pgAdmin** | 5050 | http://localhost:5050 | DB management (optional) |

---

## 🔧 Configuration

### Environment Variables (.env)

**Required**:
- `POSTGRES_PASSWORD` - PostgreSQL password (CHANGE THIS!)
- `REDIS_PASSWORD` - Redis password (CHANGE THIS!)
- `GRAFANA_PASSWORD` - Grafana admin password (CHANGE THIS!)

**Optional**:
- `LOG_LEVEL` - Application logging level (default: INFO)
- `AGENT_MODE` - Agent execution mode (default: REAL)
- `OLLAMA_HOST` - Ollama LLM endpoint (for classifier agent)

### Database Initialization

On first startup, run migrations:
```bash
docker-compose -f docker-compose.production.yml exec api alembic upgrade head
```

### Scaling

Scale API replicas:
```bash
docker-compose -f docker-compose.production.yml up -d --scale api=3
```

---

## 🧪 Testing

### API Endpoints

#### Health Check
```bash
curl http://localhost/health
```

#### List Agents
```bash
curl http://localhost/v1/mcp/tools/list_autonomous_agents
```

#### Sentiment Analysis
```bash
curl -X POST http://localhost/v1/mcp/tools/analyze_sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This product is amazing! I love it.",
    "detailed": true
  }'
```

#### System Monitoring
```bash
curl -X POST http://localhost/v1/mcp/tools/monitor_system_health \
  -H "Content-Type: application/json" \
  -d '{"detailed": true}'
```

### Load Testing

Using Apache Bench:
```bash
ab -n 1000 -c 10 -p sentiment.json -T application/json \
   http://localhost/v1/mcp/tools/analyze_sentiment
```

---

## 📈 Monitoring

### Prometheus Metrics

Access Prometheus UI: http://localhost:9090

**Key Metrics**:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `twisterlab_agent_execution_seconds` - Agent execution time
- `twisterlab_agent_errors_total` - Agent errors

### Grafana Dashboards

Access Grafana: http://localhost:3000

**Default Credentials**: admin / (password from .env)

**Pre-built Dashboards**:
1. System Overview - CPU, Memory, Network
2. API Performance - Request rates, latency, errors
3. Agent Metrics - Execution times, success rates

---

## 🔐 Security

### Production Checklist

- [ ] Change all default passwords in `.env`
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure firewall rules
- [ ] Set up authentication for API endpoints
- [ ] Enable Prometheus access restrictions
- [ ] Configure backup retention
- [ ] Review NGINX rate limiting

### SSL/TLS Setup

1. Generate SSL certificates:
```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

2. Uncomment HTTPS server block in `nginx/nginx.conf`

3. Restart NGINX:
```bash
docker-compose -f docker-compose.production.yml restart nginx
```

---

## 💾 Backup & Recovery

### Database Backup

Manual backup:
```bash
docker-compose -f docker-compose.production.yml exec postgres \
  pg_dump -U twisterlab twisterlab > backup_$(date +%Y%m%d).sql
```

Automated backup (using RealBackupAgent):
```bash
curl -X POST http://localhost/v1/mcp/tools/create_backup \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Restore

```bash
docker-compose -f docker-compose.production.yml exec -T postgres \
  psql -U twisterlab twisterlab < backup_20251211.sql
```

---

## 🐛 Troubleshooting

### API Not Starting

**Check logs**:
```bash
docker-compose -f docker-compose.production.yml logs api
```

**Common issues**:
- Database not ready → Wait for healthcheck
- Port 8000 in use → Change port mapping
- Missing environment variables → Check `.env`

### Database Connection Errors

**Verify connection**:
```bash
docker-compose -f docker-compose.production.yml exec postgres \
  psql -U twisterlab -c "SELECT version();"
```

**Reset database**:
```bash
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml up -d
```

### High Memory Usage

**Check resource usage**:
```bash
docker stats
```

**Adjust limits in `docker-compose.production.yml`**:
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 1G
```

---

## 📦 Updates

### Update Images

```bash
# Pull latest images
docker pull ghcr.io/youneselfakir0/twisterlab/api:latest
docker pull ghcr.io/youneselfakir0/twisterlab/mcp:latest

# Recreate containers
docker-compose -f docker-compose.production.yml up -d --force-recreate api mcp
```

### Rolling Update (Zero Downtime)

```bash
# Update one replica at a time
docker-compose -f docker-compose.production.yml up -d --no-deps --scale api=2 api
sleep 30
docker-compose -f docker-compose.production.yml up -d --no-deps --scale api=3 api
```

---

## 🧹 Maintenance

### Cleanup Unused Resources

```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes (CAUTION: data loss)
docker volume prune -f
```

### Database Maintenance

```bash
# Vacuum database
docker-compose -f docker-compose.production.yml exec postgres \
  psql -U twisterlab -c "VACUUM ANALYZE;"

# Check table sizes
docker-compose -f docker-compose.production.yml exec postgres \
  psql -U twisterlab -c "\dt+"
```

---

## 📊 Performance Tuning

### PostgreSQL Optimization

Edit `docker-compose.production.yml`:
```yaml
environment:
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
  POSTGRES_WORK_MEM: 16MB
```

### Redis Optimization

```yaml
command: |
  redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
  --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### NGINX Caching

Add to `nginx/nginx.conf`:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /v1/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    # ... other proxy settings
}
```

---

## 🔗 Additional Resources

- **Documentation**: `docs/`
- **API Reference**: http://localhost/docs (Swagger UI)
- **Monitoring Guide**: `docs/OPERATIONS/MONITORING.md`
- **GitHub Issues**: https://github.com/youneselfakir0/twisterlab/issues

---

## ✅ Production Readiness Checklist

- [ ] All passwords changed from defaults
- [ ] SSL/TLS certificates configured
- [ ] Backup strategy implemented
- [ ] Monitoring dashboards configured
- [ ] Log rotation enabled
- [ ] Resource limits tuned
- [ ] Health checks verified
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Security audit passed

---

**Support**: For issues, create a GitHub issue or check documentation in `docs/`
