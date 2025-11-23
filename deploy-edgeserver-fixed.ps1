# Déploiement TwisterLab sur EdgeServer
Write-Host "Deploiement TwisterLab sur EdgeServer (192.168.0.30)..." -ForegroundColor Cyan

$EdgeServerIP = "192.168.0.30"
$EdgeServerUser = "twister"

# Test connexion SSH
Write-Host "Test connexion SSH..." -ForegroundColor Yellow
try {
    $result = ssh -o ConnectTimeout=10 "$EdgeServerUser@$EdgeServerIP" "echo 'SSH OK'"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Connexion SSH etablie" -ForegroundColor Green
    } else {
        Write-Host "Impossible de se connecter a EdgeServer" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Erreur SSH: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Transfert fichiers
Write-Host "Transfert fichiers K8s..." -ForegroundColor Yellow
scp -r "k8s\*" "$EdgeServerUser@${EdgeServerIP}:~/TwisterLab/k8s/"
Write-Host "Fichiers transferes" -ForegroundColor Green

# Installation K3s
Write-Host "Installation K3s sur EdgeServer..." -ForegroundColor Yellow

# Créer script K3s temporaire
$k3sScript = @"
#!/bin/bash
set -e

echo "Installation K3s..."

# Configuration K3s
cat > /tmp/k3s-config.yaml << 'EOF'
write-kubeconfig-mode: "0644"
tls-san:
  - "192.168.0.30"
  - "edgeserver.local"
cluster-init: true
disable:
  - "servicelb"
  - "traefik"
node-label:
  - "node-type=edge-server"
  - "environment=production"
kubelet-arg:
  - "max-pods=50"
EOF

# Installation
curl -sfL https://get.k3s.io | sh -s - --config /tmp/k3s-config.yaml

# Attente
sleep 30

# Configuration kubectl
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown `$(id -u)`:`$(id -g)` ~/.kube/config
export KUBECONFIG=~/.kube/config

echo "K3s installe"
"@

# Sauvegarder et envoyer
$k3sScript | Out-File -FilePath "temp-k3s.sh" -Encoding UTF8
scp "temp-k3s.sh" "$EdgeServerUser@${EdgeServerIP}:~/install-k3s.sh"
ssh "$EdgeServerUser@$EdgeServerIP" "chmod +x ~/install-k3s.sh && ~/install-k3s.sh"
Remove-Item "temp-k3s.sh"

Write-Host "K3s installe sur EdgeServer" -ForegroundColor Green

# Installation prérequis
Write-Host "Installation prequis..." -ForegroundColor Yellow

$prereqScript = @"
#!/bin/bash
set -e

echo "Installation prequis..."

# NGINX Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx --timeout=300s -n ingress-nginx

# Cert Manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager --timeout=300s -n cert-manager

echo "Prequis installes"
"@

$prereqScript | Out-File -FilePath "temp-prereq.sh" -Encoding UTF8
scp "temp-prereq.sh" "$EdgeServerUser@${EdgeServerIP}:~/install-prereq.sh"
ssh "$EdgeServerUser@$EdgeServerIP" "chmod +x ~/install-prereq.sh && ~/install-prereq.sh"
Remove-Item "temp-prereq.sh"

Write-Host "Prequis installes" -ForegroundColor Green

# Déploiement TwisterLab
Write-Host "Deploiement TwisterLab..." -ForegroundColor Yellow

$deployScript = @"
#!/bin/bash
set -e

cd ~/TwisterLab

echo "Deploiement TwisterLab..."

# Namespace
kubectl apply -f k8s/base/namespace.yaml

# Ressources base
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secrets.yaml
kubectl apply -f k8s/base/storage.yaml

# Infrastructure
kubectl apply -f k8s/deployments/postgres.yaml
kubectl apply -f k8s/deployments/redis.yaml

# Attendre DB
kubectl wait --for=condition=ready pod -l app=twisterlab,component=database --timeout=300s -n twisterlab
kubectl wait --for=condition=ready pod -l app=twisterlab,component=cache --timeout=300s -n twisterlab

# API
kubectl apply -f k8s/deployments/api.yaml

# MCP
kubectl apply -f k8s/deployments/mcp/

# Monitoring
kubectl apply -f k8s/deployments/monitoring/

# Ingress
kubectl apply -f k8s/ingress/

echo "Deploiement termine!"
"@

$deployScript | Out-File -FilePath "temp-deploy.sh" -Encoding UTF8
scp "temp-deploy.sh" "$EdgeServerUser@${EdgeServerIP}:~/deploy-twisterlab.sh"
ssh "$EdgeServerUser@$EdgeServerIP" "chmod +x ~/deploy-twisterlab.sh && ~/deploy-twisterlab.sh"
Remove-Item "temp-deploy.sh"

Write-Host "TwisterLab deploye sur EdgeServer" -ForegroundColor Green

# Vérification
Write-Host "Verification deploiement..." -ForegroundColor Yellow

$verifyScript = @"
#!/bin/bash

echo "=== STATUS TWISTERLAB ==="
kubectl get all -n twisterlab

echo ""
echo "=== PODS STATUS ==="
kubectl get pods -n twisterlab -o wide

echo ""
echo "=== SERVICES ==="
kubectl get services -n twisterlab

echo ""
echo "=== INGRESS ==="
kubectl get ingress -n twisterlab

echo ""
echo "Verification terminee"
"@

$verifyScript | Out-File -FilePath "temp-verify.sh" -Encoding UTF8
scp "temp-verify.sh" "$EdgeServerUser@${EdgeServerIP}:~/verify.sh"
ssh "$EdgeServerUser@$EdgeServerIP" "chmod +x ~/verify.sh && ~/verify.sh"
Remove-Item "temp-verify.sh"

Write-Host ""
Write-Host "Deploiement termine sur EdgeServer!" -ForegroundColor Green
Write-Host "Services disponibles:" -ForegroundColor Cyan
Write-Host "  API: http://api.twisterlab.local" -ForegroundColor White
Write-Host "  Grafana: http://grafana.twisterlab.local" -ForegroundColor White
Write-Host "  Prometheus: http://prometheus.twisterlab.local" -ForegroundColor White