#!/bin/bash
# 🚀 SCRIPT DE DÉPLOIEMENT TWISTERLAB SUR KUBERNETES
# Date: 22 novembre 2025
# Migration complète depuis Docker Swarm

set -e

echo "🚀 Déploiement TwisterLab sur Kubernetes..."

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérification des prérequis
check_prerequisites() {
    log "Vérification des prérequis..."

    if ! command -v kubectl &> /dev/null; then
        error "kubectl n'est pas installé"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé"
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        error "Connexion au cluster Kubernetes impossible"
        exit 1
    fi

    success "Prérequis vérifiés"
}

# Création du namespace
create_namespace() {
    log "Création du namespace twisterlab..."
    kubectl apply -f k8s/base/namespace.yaml
    success "Namespace créé"
}

# Déploiement des ressources de base
deploy_base_resources() {
    log "Déploiement des ressources de base..."

    kubectl apply -f k8s/base/configmap.yaml
    kubectl apply -f k8s/base/secrets.yaml
    kubectl apply -f k8s/base/storage.yaml

    success "Ressources de base déployées"
}

# Construction et push des images
build_and_push_images() {
    log "Construction des images Docker..."

    # API Image
    if [ -f "Dockerfile" ]; then
        log "Construction de l'image API..."
        docker build -t twisterlab-api:latest .
        docker tag twisterlab-api:latest twisterlab-api:v1
        success "Image API construite"
    fi

    # MCP Agents Image
    if [ -f "mcp_agents/Dockerfile.mcp" ]; then
        log "Construction de l'image MCP..."
        docker build -f mcp_agents/Dockerfile.mcp -t twisterlab-mcp:latest .
        docker tag twisterlab-mcp:latest twisterlab-mcp:v1
        success "Image MCP construite"
    fi

    # Note: Dans un environnement réel, pousser vers un registry
    # docker push twisterlab-api:latest
    # docker push twisterlab-mcp:latest
}

# Déploiement des services de base
deploy_infrastructure() {
    log "Déploiement de l'infrastructure..."

    # PostgreSQL
    log "Déploiement PostgreSQL..."
    kubectl apply -f k8s/deployments/postgres.yaml
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=database --timeout=300s

    # Redis
    log "Déploiement Redis..."
    kubectl apply -f k8s/deployments/redis.yaml
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=cache --timeout=300s

    success "Infrastructure déployée"
}

# Déploiement de l'API
deploy_api() {
    log "Déploiement de l'API TwisterLab..."
    kubectl apply -f k8s/deployments/api.yaml
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=api --timeout=300s
    success "API déployée"
}

# Déploiement des agents MCP
deploy_mcp_agents() {
    log "Déploiement des agents MCP..."
    kubectl apply -f k8s/deployments/mcp/
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=mcp --timeout=300s
    success "Agents MCP déployés"
}

# Déploiement du monitoring
deploy_monitoring() {
    log "Déploiement du monitoring..."
    kubectl apply -f k8s/deployments/monitoring/
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=monitoring --timeout=300s
    success "Monitoring déployé"
}

# Configuration de l'Ingress
deploy_ingress() {
    log "Configuration de l'Ingress..."
    kubectl apply -f k8s/ingress/
    success "Ingress configuré"
}

# Vérification du déploiement
verify_deployment() {
    log "Vérification du déploiement..."

    # Vérification des pods
    kubectl get pods -n twisterlab

    # Vérification des services
    kubectl get services -n twisterlab

    # Tests de santé
    log "Tests de santé des services..."

    # Test API
    if kubectl exec -n twisterlab deployment/twisterlab-api -c api -- curl -f http://localhost:8000/health &> /dev/null; then
        success "API opérationnelle"
    else
        warning "API non accessible (normal si pas d'init DB)"
    fi

    # Test MCP Orchestrator
    if kubectl exec -n twisterlab deployment/mcp-orchestrator -c mcp-orchestrator -- curl -f http://localhost:8080/health &> /dev/null; then
        success "MCP Orchestrator opérationnel"
    else
        warning "MCP Orchestrator non accessible"
    fi

    success "Vérification terminée"
}

# Fonction principale
main() {
    echo "🎯 Migration TwisterLab : Docker Swarm → Kubernetes"
    echo "=================================================="

    check_prerequisites
    create_namespace
    deploy_base_resources
    build_and_push_images
    deploy_infrastructure
    deploy_api
    deploy_mcp_agents
    deploy_monitoring
    deploy_ingress
    verify_deployment

    echo ""
    success "🎉 Migration vers Kubernetes terminée avec succès!"
    echo ""
    echo "📊 Services disponibles:"
    echo "  🌐 API: http://api.twisterlab.local"
    echo "  📈 Grafana: http://grafana.twisterlab.local"
    echo "  📊 Prometheus: http://prometheus.twisterlab.local"
    echo "  🤖 MCP Orchestrator: mcp-orchestrator.twisterlab.svc.cluster.local:8080"
    echo "  📋 MCP Monitoring: mcp-monitoring.twisterlab.svc.cluster.local:8082"
    echo ""
    echo "🔧 Commandes utiles:"
    echo "  kubectl get pods -n twisterlab"
    echo "  kubectl logs -n twisterlab deployment/twisterlab-api"
    echo "  kubectl port-forward -n twisterlab svc/twisterlab-api 8000:8000"
}

# Gestion des arguments
case "${1:-}" in
    "destroy")
        log "Destruction du déploiement..."
        kubectl delete namespace twisterlab --ignore-not-found=true
        success "Déploiement détruit"
        ;;
    "status")
        kubectl get all -n twisterlab
        ;;
    "logs")
        component="${2:-api}"
        kubectl logs -n twisterlab -l app=twisterlab,component=$component --tail=100
        ;;
    *)
        main
        ;;
esac