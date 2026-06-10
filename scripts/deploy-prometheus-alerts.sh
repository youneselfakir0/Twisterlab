#!/bin/bash
# TwisterLab Prometheus Alerting Deployment Script
# This script deploys the alerting rules and verifies the setup

set -e

echo "🚀 TwisterLab Prometheus Alerting Deployment"
echo "============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Apply ConfigMap
echo -e "${YELLOW}Step 1: Applying alerting rules ConfigMap...${NC}"
kubectl apply -f k8s/monitoring/prometheus-alerts-twisterlab.yaml -n monitoring

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ConfigMap applied successfully${NC}"
else
    echo -e "${RED}✗ Failed to apply ConfigMap${NC}"
    exit 1
fi

echo ""

# Step 2: Verify ConfigMap
echo -e "${YELLOW}Step 2: Verifying ConfigMap creation...${NC}"
kubectl get configmap prometheus-twisterlab-alerts -n monitoring > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ConfigMap exists${NC}"
else
    echo -e "${RED}✗ ConfigMap not found${NC}"
    exit 1
fi

echo ""

# Step 3: Reload Prometheus
echo -e "${YELLOW}Step 3: Reloading Prometheus configuration...${NC}"
echo "   Checking for Prometheus deployment..."

# Try to find Prometheus deployment
PROM_DEPLOYMENT=$(kubectl get deployment -n monitoring -l app=prometheus -o name 2>/dev/null | head -n1)

if [ -z "$PROM_DEPLOYMENT" ]; then
    # Try alternative label
    PROM_DEPLOYMENT=$(kubectl get deployment -n monitoring -l app.kubernetes.io/name=prometheus -o name 2>/dev/null | head -n1)
fi

if [ -n "$PROM_DEPLOYMENT" ]; then
    echo "   Found: $PROM_DEPLOYMENT"
    kubectl rollout restart $PROM_DEPLOYMENT -n monitoring
    echo -e "${GREEN}✓ Prometheus reloaded${NC}"
else
    echo -e "${YELLOW}⚠ Prometheus deployment not found via labels${NC}"
    echo "   Please manually reload Prometheus or send SIGHUP signal"
fi

echo ""

# Step 4: Wait for Prometheus to be ready
echo -e "${YELLOW}Step 4: Waiting for Prometheus to become ready...${NC}"
sleep 10
echo -e "${GREEN}✓ Wait complete${NC}"

echo ""

# Step 5: Summary
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}✅ Alerting Rules Deployment Complete!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Verify rules loaded:"
echo "   kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "   Visit: http://localhost:9090/rules"
echo ""
echo "2. Check alert status:"
echo "   Visit: http://localhost:9090/alerts"
echo ""
echo "3. View in Grafana:"
echo "   Navigate to your Grafana dashboard"
echo "   Check the alerting tab"
echo ""
echo "4. Test an alert:"
echo "   kubectl scale deployment/twisterlab-agents --replicas=2 -n twisterlab"
echo "   Wait 2 minutes, then check alerts"
echo "   kubectl scale deployment/twisterlab-agents --replicas=5 -n twisterlab"
echo ""
echo "📖 Full documentation:"
echo "   docs/prometheus-alerting-setup.md"
echo ""
