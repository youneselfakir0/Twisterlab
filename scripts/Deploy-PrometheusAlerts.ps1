# TwisterLab Prometheus Alerting Deployment Script (PowerShell)
# This script deploys the alerting rules and verifies the setup

$ErrorActionPreference = "Stop"

Write-Host "🚀 TwisterLab Prometheus Alerting Deployment" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Apply ConfigMap
Write-Host "Step 1: Applying alerting rules ConfigMap..." -ForegroundColor Yellow
try {
    kubectl apply -f k8s/monitoring/prometheus-alerts-twisterlab.yaml -n monitoring
    Write-Host "✓ ConfigMap applied successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to apply ConfigMap" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Verify ConfigMap
Write-Host "Step 2: Verifying ConfigMap creation..." -ForegroundColor Yellow
try {
    kubectl get configmap prometheus-twisterlab-alerts -n monitoring | Out-Null
    Write-Host "✓ ConfigMap exists" -ForegroundColor Green
} catch {
    Write-Host "✗ ConfigMap not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Reload Prometheus
Write-Host "Step 3: Reloading Prometheus configuration..." -ForegroundColor Yellow
Write-Host "   Checking for Prometheus deployment..."

# Try to find Prometheus deployment
$promDeployment = kubectl get deployment -n monitoring -l app=prometheus -o name 2>$null | Select-Object -First 1

if (-not $promDeployment) {
    # Try alternative label
    $promDeployment = kubectl get deployment -n monitoring -l app.kubernetes.io/name=prometheus -o name 2>$null | Select-Object -First 1
}

if ($promDeployment) {
    Write-Host "   Found: $promDeployment"
    kubectl rollout restart $promDeployment -n monitoring
    Write-Host "✓ Prometheus reloaded" -ForegroundColor Green
} else {
    Write-Host "⚠ Prometheus deployment not found via labels" -ForegroundColor Yellow
    Write-Host "   Please manually reload Prometheus or send SIGHUP signal"
}

Write-Host ""

# Step 4: Wait for Prometheus to be ready
Write-Host "Step 4: Waiting for Prometheus to become ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
Write-Host "✓ Wait complete" -ForegroundColor Green

Write-Host ""

# Step 5: Summary
Write-Host "=============================================" -ForegroundColor Green
Write-Host "✅ Alerting Rules Deployment Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Verify rules loaded:"
Write-Host "   kubectl port-forward -n monitoring svc/prometheus 9090:9090"
Write-Host "   Visit: http://localhost:9090/rules"
Write-Host ""
Write-Host "2. Check alert status:"
Write-Host "   Visit: http://localhost:9090/alerts"
Write-Host ""
Write-Host "3. View in Grafana:"
Write-Host "   Navigate to your Grafana dashboard"
Write-Host "   Check the alerting tab"
Write-Host ""
Write-Host "4. Test an alert:"
Write-Host "   kubectl scale deployment/twisterlab-agents --replicas=2 -n twisterlab"
Write-Host "   Wait 2 minutes, then check alerts"
Write-Host "   kubectl scale deployment/twisterlab-agents --replicas=5 -n twisterlab"
Write-Host ""
Write-Host "📖 Full documentation:"
Write-Host "   docs/prometheus-alerting-setup.md"
Write-Host ""
