# 🚀 DÉPLOIEMENT TWISTERLAB SUR EDGESERVER (192.168.0.30)
# Via SSH - Installation K3s + TwisterLab
# Date: 22 novembre 2025

Write-Host "🚀 Déploiement TwisterLab sur EdgeServer (192.168.0.30)..." -ForegroundColor Cyan

# Configuration
$EdgeServerIP = "192.168.0.30"
$EdgeServerUser = "twister"
$LocalK8sPath = "C:\TwisterLab\k8s"

# Fonctions utilitaires
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "ℹ️  $Message" -ForegroundColor Blue }

# Test de connexion SSH
function Test-SSHConnection {
    Write-Info "Test de connexion SSH vers EdgeServer..."

    try {
        $result = ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$EdgeServerUser@$EdgeServerIP" "echo 'SSH OK'"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Connexion SSH établie"
            return $true
        }
    } catch {
        Write-Error "Impossible de se connecter à EdgeServer"
        return $false
    }
}

# Transfert des fichiers K8s vers EdgeServer
function Copy-K8sFiles {
    Write-Info "Transfert des manifests Kubernetes vers EdgeServer..."

    # Créer répertoire sur EdgeServer
    ssh "$EdgeServerUser@$EdgeServerIP" "mkdir -p ~/TwisterLab/k8s"

    # Copier tous les manifests
    scp -r "$LocalK8sPath\*" "$EdgeServerUser@$EdgeServerIP`:~/TwisterLab/k8s/"

    Write-Success "Manifests transférés"
}

# Installation de K3s sur EdgeServer
function Install-K3sOnEdgeServer {
    Write-Info "Installation de K3s sur EdgeServer..."

    $k3sInstallScript = @"
#!/bin/bash
set -e

echo "Installation de K3s sur EdgeServer..."

# Créer configuration K3s optimisée
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

# Installer K3s
curl -sfL https://get.k3s.io | sh -s - --config /tmp/k3s-config.yaml

# Attendre démarrage
sleep 30

# Configurer kubectl
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
export KUBECONFIG=~/.kube/config

echo "K3s installé avec succès"
"@

    # Envoyer et exécuter le script
    ssh "$EdgeServerUser@$EdgeServerIP" "cat > ~/install-k3s.sh" < $k3sInstallScript
    ssh "$EdgeServerUser@$EdgeServerIP" "chmod +x ~/install-k3s.sh && ~/install-k3s.sh"

    Write-Success "K3s installé sur EdgeServer"
}

# Installation des prérequis sur EdgeServer
function Install-PrerequisitesOnEdgeServer {
    Write-Info "Installation des prérequis sur EdgeServer..."

    $prereqScript = @"
#!/bin/bash
set -e

echo "Installation des prérequis..."

# NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Attendre NGINX
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx --timeout=300s -n ingress-nginx

# Cert Manager (optionnel)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager --timeout=300s -n cert-manager

echo "Prérequis installés"
"@

    ssh "$EdgeServerUser@$EdgeServerIP" "cat > ~/install-prereq.sh" < $prereqScript
    ssh "$EdgeServerUser@$EdgeServerIP" "chmod +x ~/install-prereq.sh && ~/install-prereq.sh"

    Write-Success "Prérequis installés sur EdgeServer"
}

# Déploiement de TwisterLab sur EdgeServer
function Deploy-TwisterLabOnEdgeServer {
    Write-Info "Déploiement de TwisterLab sur EdgeServer..."

    $deployScript = @"
#!/bin/bash
set -e

cd ~/TwisterLab

echo "Déploiement TwisterLab..."

# Namespace
kubectl apply -f k8s/base/namespace.yaml

# Ressources de base
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secrets.yaml
kubectl apply -f k8s/base/storage.yaml

# Infrastructure
echo "Déploiement infrastructure..."
kubectl apply -f k8s/deployments/postgres.yaml
kubectl apply -f k8s/deployments/redis.yaml

# Attendre DB
kubectl wait --for=condition=ready pod -l app=twisterlab,component=database --timeout=300s -n twisterlab
kubectl wait --for=condition=ready pod -l app=twisterlab,component=cache --timeout=300s -n twisterlab

# API
echo "Déploiement API..."
kubectl apply -f k8s/deployments/api.yaml

# MCP Agents
echo "Déploiement agents MCP..."
kubectl apply -f k8s/deployments/mcp/

# Monitoring
echo "Déploiement monitoring..."
kubectl apply -f k8s/deployments/monitoring/

# Ingress
echo "Configuration Ingress..."
kubectl apply -f k8s/ingress/

echo "Déploiement terminé!"
"@

    ssh "$EdgeServerUser@$EdgeServerIP" "cat > ~/deploy-twisterlab.sh" < $deployScript
    ssh "$EdgeServerUser@$EdgeServerIP" "chmod +x ~/deploy-twisterlab.sh && ~/deploy-twisterlab.sh"

    Write-Success "TwisterLab déployé sur EdgeServer"
}

# Vérification du déploiement
function Verify-DeploymentOnEdgeServer {
    Write-Info "Vérification du déploiement sur EdgeServer..."

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
echo "=== HEALTH CHECKS ==="
# Test API
if kubectl exec -n twisterlab deployment/twisterlab-api -c api -- curl -f http://localhost:8000/health 2>/dev/null; then
    echo "✅ API opérationnelle"
else
    echo "⚠️  API en cours de démarrage"
fi

echo "Vérification terminée"
"@

    ssh "$EdgeServerUser@$EdgeServerIP" "cat > ~/verify-deployment.sh" < $verifyScript
    ssh "$EdgeServerUser@$EdgeServerIP" "chmod +x ~/verify-deployment.sh && ~/verify-deployment.sh"

    Write-Success "Vérification terminée"
}

# Fonction principale
function Invoke-EdgeServerDeployment {
    Write-Host "🎯 Déploiement TwisterLab sur EdgeServer" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan

    # Test connexion
    if (!(Test-SSHConnection)) {
        Write-Error "Impossible de se connecter à EdgeServer. Vérifiez la connexion réseau."
        exit 1
    }

    # Transfert fichiers
    Copy-K8sFiles

    # Installation K3s
    Install-K3sOnEdgeServer

    # Prérequis
    Install-PrerequisitesOnEdgeServer

    # Déploiement
    Deploy-TwisterLabOnEdgeServer

    # Vérification
    Verify-DeploymentOnEdgeServer

    Write-Host ""
    Write-Success "🎉 Déploiement terminé sur EdgeServer!"
    Write-Host ""
    Write-Info "Services disponibles:"
    Write-Host "  🌐 API: http://api.twisterlab.local" -ForegroundColor Cyan
    Write-Host "  📈 Grafana: http://grafana.twisterlab.local" -ForegroundColor Cyan
    Write-Host "  📊 Prometheus: http://prometheus.twisterlab.local" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Commandes de gestion sur EdgeServer:"
    Write-Host "  kubectl get pods -n twisterlab" -ForegroundColor Yellow
    Write-Host "  kubectl logs -n twisterlab -f deployment/twisterlab-api" -ForegroundColor Yellow
}

# Point d'entrée
try {
    Invoke-EdgeServerDeployment
} catch {
    Write-Error "Erreur lors du déploiement: $($_.Exception.Message)"
    exit 1
}