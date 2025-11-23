# Deploiement TwisterLab sur K3s
Write-Host "Deploiement TwisterLab sur K3s..." -ForegroundColor Cyan

# Verifier kubectl
try {
    kubectl cluster-info | Out-Null
    Write-Host "Cluster K3s operationnel" -ForegroundColor Green
} catch {
    Write-Host "K3s non accessible" -ForegroundColor Red
    exit 1
}

# Construction images
Write-Host "Construction images..." -ForegroundColor Yellow
if (Test-Path "Dockerfile") {
    docker build -t twisterlab-api:latest .
    Write-Host "Image API construite" -ForegroundColor Green
}

if (Test-Path "mcp_agents\Dockerfile.mcp") {
    docker build -f mcp_agents\Dockerfile.mcp -t twisterlab-mcp:latest .
    Write-Host "Image MCP construite" -ForegroundColor Green
}

# Deploiement manifests
Write-Host "Deploiement manifests..." -ForegroundColor Yellow

kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secrets.yaml
kubectl apply -f k8s/base/storage.yaml

kubectl apply -f k8s/deployments/postgres.yaml
kubectl apply -f k8s/deployments/redis.yaml
kubectl apply -f k8s/deployments/api.yaml
kubectl apply -f k8s/deployments/mcp/
kubectl apply -f k8s/deployments/monitoring/
kubectl apply -f k8s/ingress/

Write-Host "Attente demarrage services..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verification
Write-Host "Verification deploiement..." -ForegroundColor Yellow
kubectl get pods -n twisterlab

Write-Host ""
Write-Host "Deploiement termine!" -ForegroundColor Green
Write-Host "Services: http://api.twisterlab.local" -ForegroundColor Cyan