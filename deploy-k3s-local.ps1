# 🚀 DÉPLOIEMENT TWISTERLAB SUR K3S LOCAL (COREOS)
# Pour environnement de développement/test
# Date: 22 novembre 2025

Write-Host "🚀 Déploiement TwisterLab sur K3s local..." -ForegroundColor Cyan

# Configuration
$K3sPath = "C:\TwisterLab\k8s"
$Namespace = "twisterlab"

# Fonctions utilitaires
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "ℹ️  $Message" -ForegroundColor Blue }

# Vérification K3s local
function Test-K3sLocal {
    Write-Info "Vérification de K3s local..."

    try {
        $result = kubectl cluster-info
        Write-Success "Cluster K3s opérationnel"
        return $true
    } catch {
        Write-Warning "K3s non détecté. Installation recommandée:"
        Write-Host "  curl -sfL https://get.k3s.io | sh -" -ForegroundColor Yellow
        Write-Host "  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml" -ForegroundColor Yellow
        return $false
    }
}

# Construction des images
function Build-Images {
    Write-Info "Construction des images Docker..."

    Push-Location "C:\TwisterLab"

    # Image API
    if (Test-Path "Dockerfile") {
        Write-Info "Construction image API..."
        docker build -t twisterlab-api:latest .
        Write-Success "Image API construite"
    }

    # Image MCP
    if (Test-Path "mcp_agents\Dockerfile.mcp") {
        Write-Info "Construction image MCP..."
        docker build -f mcp_agents\Dockerfile.mcp -t twisterlab-mcp:latest .
        Write-Success "Image MCP construite"
    }

    Pop-Location
}

# Déploiement étape par étape
function Deploy-StepByStep {
    Write-Info "Déploiement étape par étape..."

    # Namespace
    Write-Info "Création namespace..."
    kubectl apply -f "$K3sPath\base\namespace.yaml"
    Write-Success "Namespace créé"

    # Base resources
    Write-Info "Ressources de base..."
    kubectl apply -f "$K3sPath\base\configmap.yaml"
    kubectl apply -f "$K3sPath\base\secrets.yaml"
    kubectl apply -f "$K3sPath\base\storage.yaml"
    Write-Success "Ressources de base déployées"

    # Infrastructure
    Write-Info "Infrastructure (PostgreSQL + Redis)..."
    kubectl apply -f "$K3sPath\deployments\postgres.yaml"
    kubectl apply -f "$K3sPath\deployments\redis.yaml"

    Write-Info "Attente démarrage infrastructure..."
    Start-Sleep -Seconds 30
    Write-Success "Infrastructure déployée"

    # API
    Write-Info "API TwisterLab..."
    kubectl apply -f "$K3sPath\deployments\api.yaml"
    Write-Success "API déployée"

    # MCP Agents
    Write-Info "Agents MCP..."
    kubectl apply -f "$K3sPath\deployments\mcp\"
    Write-Success "Agents MCP déployés"

    # Monitoring
    Write-Info "Monitoring (Prometheus + Grafana)..."
    kubectl apply -f "$K3sPath\deployments\monitoring\"
    Write-Success "Monitoring déployé"

    # Ingress
    Write-Info "Configuration Ingress..."
    kubectl apply -f "$K3sPath\ingress\"
    Write-Success "Ingress configuré"
}

# Vérification du déploiement
function Verify-Deployment {
    Write-Info "Vérification du déploiement..."

    Write-Host ""
    Write-Host "=== PODS STATUS ===" -ForegroundColor Yellow
    kubectl get pods -n $Namespace

    Write-Host ""
    Write-Host "=== SERVICES ===" -ForegroundColor Yellow
    kubectl get services -n $Namespace

    Write-Host ""
    Write-Host "=== INGRESS ===" -ForegroundColor Yellow
    kubectl get ingress -n $Namespace

    Write-Host ""
    Write-Host "=== HEALTH CHECKS ===" -ForegroundColor Yellow

    # Test API
    try {
        kubectl exec -n $Namespace deployment/twisterlab-api -c api -- curl -f http://localhost:8000/health | Out-Null
        Write-Success "API opérationnelle"
    } catch {
        Write-Warning "API en cours de démarrage"
    }

    # Test MCP
    try {
        kubectl exec -n $Namespace deployment/mcp-orchestrator -c mcp-orchestrator -- curl -f http://localhost:8080/health | Out-Null
        Write-Success "MCP Orchestrator opérationnel"
    } catch {
        Write-Warning "MCP en cours de démarrage"
    }
}

# Fonction principale
function Invoke-K3sDeployment {
    Write-Host "🎯 Déploiement TwisterLab sur K3s local" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan

    # Vérifications
    if (!(Test-K3sLocal)) {
        Write-Error "K3s local non opérationnel"
        exit 1
    }

    # Construction images
    Build-Images

    # Déploiement
    Deploy-StepByStep

    # Vérification
    Start-Sleep -Seconds 10
    Verify-Deployment

    Write-Host ""
    Write-Success "🎉 Déploiement terminé sur K3s local!"
    Write-Host ""
    Write-Info "Services disponibles:"
    Write-Host "  🌐 API: http://api.twisterlab.local" -ForegroundColor Cyan
    Write-Host "  📈 Grafana: http://grafana.twisterlab.local" -ForegroundColor Cyan
    Write-Host "  📊 Prometheus: http://prometheus.twisterlab.local" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Commandes de gestion:"
    Write-Host "  kubectl get pods -n twisterlab" -ForegroundColor Yellow
    Write-Host "  kubectl logs -n twisterlab -f deployment/twisterlab-api" -ForegroundColor Yellow
    Write-Host "  kubectl port-forward -n twisterlab svc/twisterlab-api 8000:8000" -ForegroundColor Yellow
}

# Point d'entrée
try {
    Invoke-K3sDeployment
} catch {
    Write-Error "Erreur lors du deploiement: $($_.Exception.Message)"
    exit 1
}