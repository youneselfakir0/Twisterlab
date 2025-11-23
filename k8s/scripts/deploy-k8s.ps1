# 🚀 SCRIPT DE DÉPLOIEMENT TWISTERLAB SUR KUBERNETES (WINDOWS)
# Date: 22 novembre 2025
# Migration complète depuis Docker Swarm

param(
    [string]$Action = "deploy",
    [string]$Component = "all"
)

# Configuration
$Namespace = "twisterlab"
$K8sPath = ".\k8s"

# Couleurs pour PowerShell
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Blue }

# Vérification des prérequis
function Test-Prerequisites {
    Write-Info "Vérification des prérequis..."

    # Vérifier kubectl
    if (!(Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-Error "kubectl n'est pas installé ou pas dans le PATH"
        exit 1
    }

    # Vérifier connexion cluster
    try {
        kubectl cluster-info | Out-Null
    } catch {
        Write-Error "Connexion au cluster Kubernetes impossible"
        exit 1
    }

    # Vérifier Docker
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker n'est pas installé"
        exit 1
    }

    Write-Success "Prérequis vérifiés"
}

# Création du namespace
function New-TwisterLabNamespace {
    Write-Info "Création du namespace $Namespace..."
    kubectl apply -f "$K8sPath\base\namespace.yaml"
    Write-Success "Namespace créé"
}

# Déploiement des ressources de base
function Install-BaseResources {
    Write-Info "Déploiement des ressources de base..."
    kubectl apply -f "$K8sPath\base\configmap.yaml"
    kubectl apply -f "$K8sPath\base\secrets.yaml"
    kubectl apply -f "$K8sPath\base\storage.yaml"
    Write-Success "Ressources de base déployées"
}

# Construction des images
function Build-DockerImages {
    Write-Info "Construction des images Docker..."

    # API Image
    if (Test-Path "Dockerfile") {
        Write-Info "Construction de l'image API..."
        docker build -t twisterlab-api:latest .
        docker tag twisterlab-api:latest twisterlab-api:v1
        Write-Success "Image API construite"
    }

    # MCP Agents Image
    if (Test-Path "mcp_agents\Dockerfile.mcp") {
        Write-Info "Construction de l'image MCP..."
        docker build -f mcp_agents\Dockerfile.mcp -t twisterlab-mcp:latest .
        docker tag twisterlab-mcp:latest twisterlab-mcp:v1
        Write-Success "Image MCP construite"
    }
}

# Déploiement de l'infrastructure
function Install-Infrastructure {
    Write-Info "Déploiement de l'infrastructure..."

    # PostgreSQL
    Write-Info "Déploiement PostgreSQL..."
    kubectl apply -f "$K8sPath\deployments\postgres.yaml"
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=database --timeout=300s -n $Namespace

    # Redis
    Write-Info "Déploiement Redis..."
    kubectl apply -f "$K8sPath\deployments\redis.yaml"
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=cache --timeout=300s -n $Namespace

    Write-Success "Infrastructure déployée"
}

# Déploiement de l'API
function Install-API {
    Write-Info "Déploiement de l'API TwisterLab..."
    kubectl apply -f "$K8sPath\deployments\api.yaml"
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=api --timeout=300s -n $Namespace
    Write-Success "API déployée"
}

# Déploiement des agents MCP
function Install-MCPAgents {
    Write-Info "Déploiement des agents MCP..."
    kubectl apply -f "$K8sPath\deployments\mcp\"
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=mcp --timeout=300s -n $Namespace
    Write-Success "Agents MCP déployés"
}

# Déploiement du monitoring
function Install-Monitoring {
    Write-Info "Déploiement du monitoring..."
    kubectl apply -f "$K8sPath\deployments\monitoring\"
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=monitoring --timeout=300s -n $Namespace
    Write-Success "Monitoring déployé"
}

# Configuration de l'Ingress
function Install-Ingress {
    Write-Info "Configuration de l'Ingress..."
    kubectl apply -f "$K8sPath\ingress\"
    Write-Success "Ingress configuré"
}

# Vérification du déploiement
function Test-Deployment {
    Write-Info "Vérification du déploiement..."

    # Afficher les pods
    Write-Info "Pods actifs:"
    kubectl get pods -n $Namespace

    # Afficher les services
    Write-Info "Services:"
    kubectl get services -n $Namespace

    Write-Success "Vérification terminée"
}

# Fonction principale de déploiement
function Install-TwisterLab {
    Write-Host "🎯 Migration TwisterLab : Docker Swarm → Kubernetes" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan

    Test-Prerequisites
    New-TwisterLabNamespace
    Install-BaseResources
    Build-DockerImages
    Install-Infrastructure
    Install-API
    Install-MCPAgents
    Install-Monitoring
    Install-Ingress
    Test-Deployment

    Write-Host ""
    Write-Success "🎉 Migration vers Kubernetes terminée avec succès!"
    Write-Host ""
    Write-Host "📊 Services disponibles:" -ForegroundColor Cyan
    Write-Host "  🌐 API: http://api.twisterlab.local" -ForegroundColor White
    Write-Host "  📈 Grafana: http://grafana.twisterlab.local" -ForegroundColor White
    Write-Host "  📊 Prometheus: http://prometheus.twisterlab.local" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Commandes utiles:" -ForegroundColor Yellow
    Write-Host "  kubectl get pods -n $Namespace" -ForegroundColor White
    Write-Host "  kubectl logs -n $Namespace deployment/twisterlab-api" -ForegroundColor White
    Write-Host "  kubectl port-forward -n $Namespace svc/twisterlab-api 8000:8000" -ForegroundColor White
}

# Gestion des actions
switch ($Action) {
    "deploy" {
        if ($Component -eq "all") {
            Install-TwisterLab
        } else {
            Write-Error "Composant spécifique non implémenté: $Component"
        }
    }
    "destroy" {
        Write-Info "Destruction du déploiement..."
        kubectl delete namespace $Namespace --ignore-not-found=true
        Write-Success "Déploiement détruit"
    }
    "status" {
        kubectl get all -n $Namespace
    }
    "logs" {
        if ($Component -eq "all") { $Component = "api" }
        kubectl logs -n $Namespace -l app=twisterlab,component=$Component --tail=100
    }
    default {
        Write-Error "Action inconnue: $Action"
        Write-Host "Actions disponibles: deploy, destroy, status, logs" -ForegroundColor Yellow
    }
}