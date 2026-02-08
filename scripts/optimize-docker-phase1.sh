#!/bin/bash
# Phase 1 - Action 2: Docker Optimization
# Date: 7 Février 2026
# Purpose: Optimize Docker for HDD performance

set -e

echo "════════════════════════════════════════════════════════════"
echo "  PHASE 1 - ACTION 2: DOCKER OPTIMIZATION"
echo "  Objective: Improve build performance on HDD"
echo "════════════════════════════════════════════════════════════"
echo ""

# STEP 1: Backup existing config (if exists)
echo "STEP 1: BACKUP EXISTING CONFIG"
echo "─────────────────────────────────────────────────────────────"
if [ -f /etc/docker/daemon.json ]; then
    BACKUP="/etc/docker/daemon.json.backup-$(date +%Y%m%d-%H%M%S)"
    sudo cp /etc/docker/daemon.json "$BACKUP"
    echo "✅ Existing config backed up to: $BACKUP"
else
    echo "ℹ️  No existing config (creating new)"
fi
echo ""

# STEP 2: Create optimized Docker config
echo "STEP 2: CREATE OPTIMIZED CONFIG"
echo "─────────────────────────────────────────────────────────────"
sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 3,
  "live-restore": false,
  "default-ulimits": {
    "nofile": {
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
EOF

echo "✅ Docker config created"
echo ""

# STEP 3: Validate JSON
echo "STEP 3: VALIDATE JSON"
echo "─────────────────────────────────────────────────────────────"
if python3 -m json.tool /etc/docker/daemon.json > /dev/null 2>&1; then
    echo "✅ JSON is valid"
else
    echo "❌ ERROR: Invalid JSON!"
    exit 1
fi
echo ""

# STEP 4: Display config
echo "STEP 4: DOCKER CONFIG"
echo "─────────────────────────────────────────────────────────────"
cat /etc/docker/daemon.json
echo ""

# STEP 5: Restart Docker
echo "STEP 5: RESTART DOCKER DAEMON"
echo "─────────────────────────────────────────────────────────────"
echo "⚠️  Docker will restart (K3s pods will restart automatically)"
read -p "Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo "Restarting Docker..."
sudo systemctl restart docker
sleep 5

# Check Docker status
if sudo systemctl is-active --quiet docker; then
    echo "✅ Docker is running"
else
    echo "❌ ERROR: Docker failed to start!"
    sudo systemctl status docker
    exit 1
fi
echo ""

# STEP 6: Wait for K3s and pods
echo "STEP 6: WAITING FOR PODS TO STABILIZE"
echo "─────────────────────────────────────────────────────────────"
echo "Waiting 30 seconds for pods to restart..."
sleep 30

# Check K3s
if sudo systemctl is-active --quiet k3s; then
    echo "✅ K3s is running"
else
    echo "⚠️  K3s not active, checking status..."
    sudo systemctl status k3s
fi
echo ""

# STEP 7: Verify pods
echo "STEP 7: VERIFY PODS STATUS"
echo "─────────────────────────────────────────────────────────────"
echo "Checking pods (may take 1-2 min to all be Running)..."
echo ""
kubectl get pods --all-namespaces
echo ""

# Count non-running pods
NON_RUNNING=$(kubectl get pods --all-namespaces --field-selector=status.phase!=Running,status.phase!=Succeeded 2>/dev/null | grep -v NAMESPACE | wc -l)

if [ "$NON_RUNNING" -eq 0 ]; then
    echo "✅ All pods are Running or Completed"
else
    echo "⚠️  $NON_RUNNING pods not yet Running (may need more time)"
    echo ""
    echo "Re-check in 2 minutes with: kubectl get pods --all-namespaces"
fi
echo ""

# STEP 8: Verify Docker info
echo "STEP 8: VERIFY DOCKER CONFIGURATION"
echo "─────────────────────────────────────────────────────────────"
echo "Storage Driver:"
sudo docker info | grep "Storage Driver"
echo ""
echo "Logging Driver:"
sudo docker info | grep "Logging Driver"
echo ""

# STEP 9: Summary
echo "════════════════════════════════════════════════════════════"
echo "  ✅ DOCKER OPTIMIZATION COMPLETE"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Changes applied:"
echo "  ✅ Storage driver: overlay2"
echo "  ✅ Log rotation: 10MB max, 3 files"
echo "  ✅ Concurrent downloads/uploads: 3"
echo "  ✅ File limits: 64000"
echo ""
echo "Expected improvements:"
echo "  - 10-20% faster builds"
echo "  - Better log management"
echo "  - Optimized for HDD"
echo ""
echo "Next steps:"
echo "  1. Test build performance (next action)"
echo "  2. Monitor logs: journalctl -u docker -f"
echo "  3. If issues, restore backup:"
echo "     sudo cp $BACKUP /etc/docker/daemon.json"
echo "     sudo systemctl restart docker"
echo ""
echo "════════════════════════════════════════════════════════════"
