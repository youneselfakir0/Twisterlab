# MCP Services Rebuild - Quick Start Guide

**Status:** MCP services intentionally disabled due to Docker build issues  
**Cluster Health:** ✅ HEALTHY (all other services running)  
**Created:** 2026-02-04

---

## 🚀 FASTEST METHOD (RECOMMENDED)

### Option B: Build Locally & Import (15 minutes)

This bypasses the slow Docker daemon on EdgeServer.

```powershell
# Step 1: Build on Windows machine
cd C:\Users\Administrator\Documents\twisterlab

docker build -t twisterlab/mcp-unified:latest `
  -f deploy/docker/Dockerfile.mcp-fast .

# Step 2: Save and compress
docker save twisterlab/mcp-unified:latest | gzip > mcp-unified.tar.gz

# Step 3: Transfer to EdgeServer
scp mcp-unified.tar.gz twister@192.168.0.30:/tmp/

# Step 4: Import to K3s (on EdgeServer)
ssh twister@192.168.0.30 `
  "gunzip -c /tmp/mcp-unified.tar.gz | sudo k3s ctr images import -"

# Step 5: Verify import
ssh twister@192.168.0.30 "sudo k3s crictl images | grep mcp-unified"

# Step 6: Update deployments
kubectl set image deployment/mcp-server `
  mcp-server=twisterlab/mcp-unified:latest -n default

kubectl set image deployment/mcp-unified `
  mcp-unified=twisterlab/mcp-unified:latest -n twisterlab

kubectl set image deployment/mcp-unified `
  mcp-unified=twisterlab/mcp-unified:latest -n twisterlab-dev

# Step 7: Scale up
kubectl scale deployment mcp-server --replicas=1 -n default
kubectl scale deployment mcp-unified --replicas=1 -n twisterlab  
kubectl scale deployment mcp-unified --replicas=1 -n twisterlab-dev

# Step 8: Monitor deployment
kubectl get pods -n default -l app=mcp-server -w
kubectl get pods -n twisterlab -l app=mcp-unified -w
kubectl get pods -n twisterlab-dev -l app=mcp-unified -w

# Step 9: Check logs
kubectl logs -n twisterlab -l app=mcp-unified --tail=50

# Step 10: Recreate HPA (optional)
kubectl apply -f k8s/deployments/mcp-unified-hpa.yaml

# Step 11: Cleanup
rm mcp-unified.tar.gz
ssh twister@192.168.0.30 "rm /tmp/mcp-unified.tar.gz"
```

**Expected Duration:** 10-15 minutes

---

## 🏢 PRODUCTION METHOD (CI/CD)

### Option C: GitHub Container Registry

```powershell
# Step 1: Build and tag
docker build -t ghcr.io/youneselfakir0/twisterlab/mcp-unified:latest `
  -f deploy/docker/Dockerfile.mcp-fast .

# Step 2: Tag with version
docker tag ghcr.io/youneselfakir0/twisterlab/mcp-unified:latest `
  ghcr.io/youneselfakir0/twisterlab/mcp-unified:v1.0.0

# Step 3: Push to registry
docker push ghcr.io/youneselfakir0/twisterlab/mcp-unified:latest
docker push ghcr.io/youneselfakir0/twisterlab/mcp-unified:v1.0.0

# Step 4: Update K8s deployments
kubectl set image deployment/mcp-server `
  mcp-server=ghcr.io/youneselfakir0/twisterlab/mcp-unified:v1.0.0 -n default

kubectl set image deployment/mcp-unified `
  mcp-unified=ghcr.io/youneselfakir0/twisterlab/mcp-unified:v1.0.0 -n twisterlab

kubectl set image deployment/mcp-unified `
  mcp-unified=ghcr.io/youneselfakir0/twisterlab/mcp-unified:v1.0.0 -n twisterlab-dev

# Step 5: Scale up (same as Option B steps 7-11)
```

---

## 🔧 DEBUGGING METHOD

### Option A: Fix Docker on EdgeServer First

Only use this if you want to debug the Docker performance issues.

```bash
# SSH to EdgeServer
ssh twister@192.168.0.30

# Check Docker daemon logs
sudo journalctl -u docker -n 200 --no-pager

# Check Docker disk usage
sudo docker system df -v

# Test simple build
echo "FROM alpine:latest" | sudo docker build -t test -

# If build is fast, Docker is OK. If slow, investigate:
# - Network: ping pypi.org
# - Disk I/O: sudo iotop
# - Docker restart: sudo systemctl restart docker

# Once Docker is healthy, retry build:
cd /tmp/mcp-fast-build
sudo docker build -t twisterlab/mcp-unified:latest -f Dockerfile .
sudo docker save twisterlab/mcp-unified:latest | sudo k3s ctr images import -

# Then continue with Option B steps 6-11
```

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify:

- [ ] All 3 MCP pods are Running (1/1 Ready)
- [ ] No CrashLoopBackOff or ImagePullBackOff
- [ ] Health endpoints responding:
  ```bash
  kubectl exec -n twisterlab -l app=mcp-unified -- curl -s http://localhost:8080/health
  ```
- [ ] Logs show no errors:
  ```bash
  kubectl logs -n twisterlab -l app=mcp-unified --tail=100
  ```
- [ ] HPA showing valid metrics (not `<unknown>`)
- [ ] Services accessible via NodePort

---

## 🎯 EXPECTED ENDPOINTS

After successful deployment:

| Service | Namespace | Port | URL |
|---------|-----------|------|-----|
| mcp-server | default | N/A | Internal only |
| mcp-unified | twisterlab | 30080 | http://192.168.0.30:30080 |
| mcp-unified | twisterlab-dev | 31080 | http://192.168.0.30:31080 |

---

## 📝 TROUBLESHOOTING

### Pods stuck in ImagePullBackOff
```bash
# Check if image exists in K3s
ssh twister@192.168.0.30 "sudo k3s crictl images | grep mcp"

# If missing, re-import image
```

### Pods CrashLoopBackOff  
```bash
# Check logs
kubectl logs -n twisterlab -l app=mcp-unified --tail=100

# Common issues:
# - Missing environment variables
# - Database connection failure  
# - Redis connection failure
# - Missing Python modules
```

### HPA shows `<unknown>` metrics
```bash
# Wait 60-90 seconds for metrics-server to scrape
# If still unknown, check pod is actually running and healthy
```

---

## 📊 SUCCESS CRITERIA

✅ **Deployment Successful** when:
1. All MCP pods show `1/1 Ready`
2. Health endpoints return 200 OK
3. No error logs in last 100 lines
4. HPA shows actual CPU/memory percentages  
5. Services accessible via curl/browser

---

**Last Updated:** 2026-02-04  
**Next Review:** After MCP rebuild completion
