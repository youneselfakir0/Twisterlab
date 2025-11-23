# 🚀 SCRIPT DÉPLOIEMENT TWISTERLAB SUR K3S
# Optimisé pour Edge Server et environnements légers
# Date: 22 novembre 2025

#!/bin/bash
set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Configuration K3s optimisée pour Edge Server
K3S_CONFIG="
# K3s configuration pour Edge Server
# /etc/rancher/k3s/config.yaml

write-kubeconfig-mode: \"0644\"
tls-san:
  - \"192.168.0.30\"
  - \"edgeserver.local\"
cluster-init: true
disable:
  - \"servicelb\"
  - \"traefik\"
node-label:
  - \"node-type=edge-server\"
  - \"environment=production\"
kubelet-arg:
  - \"max-pods=50\"
"

# Fonction d'installation K3s
install_k3s() {
    log "Installation de K3s sur Edge Server..."

    # Créer la configuration K3s
    echo "$K3S_CONFIG" | sudo tee /etc/rancher/k3s/config.yaml > /dev/null

    # Installer K3s
    curl -sfL https://get.k3s.io | sh -s - --config /etc/rancher/k3s/config.yaml

    # Attendre que K3s soit prêt
    log "Attente du démarrage de K3s..."
    sleep 30

    # Vérifier l'installation
    if sudo k3s kubectl get nodes &>/dev/null; then
        success "K3s installé et opérationnel"
    else
        error "Échec de l'installation K3s"
        exit 1
    fi

    # Configurer kubectl
    mkdir -p ~/.kube
    sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
    sudo chown $(id -u):$(id -g) ~/.kube/config
    export KUBECONFIG=~/.kube/config

    success "kubectl configuré"
}

# Fonction d'installation des prérequis
install_prerequisites() {
    log "Installation des prérequis..."

    # NGINX Ingress Controller
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

    # Attendre que NGINX soit prêt
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx --timeout=300s -n ingress-nginx

    # Cert Manager (optionnel pour TLS)
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager --timeout=300s -n cert-manager

    success "Prérequis installés"
}

# Fonction de déploiement optimisé pour K3s
deploy_optimized() {
    log "Déploiement TwisterLab optimisé pour K3s..."

    # Créer namespace
    kubectl apply -f k8s/base/namespace.yaml

    # Déployer stockage (utiliser local-path provisioner de K3s)
    kubectl apply -f k8s/base/storage.yaml

    # ConfigMaps et Secrets
    kubectl apply -f k8s/base/configmap.yaml
    kubectl apply -f k8s/base/secrets.yaml

    # Infrastructure de base
    log "Déploiement de l'infrastructure..."
    kubectl apply -f k8s/deployments/postgres.yaml
    kubectl apply -f k8s/deployments/redis.yaml

    # Attendre que la base de données soit prête
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=database --timeout=300s -n twisterlab
    kubectl wait --for=condition=ready pod -l app=twisterlab,component=cache --timeout=300s -n twisterlab

    # API
    log "Déploiement de l'API..."
    kubectl apply -f k8s/deployments/api.yaml

    # Agents MCP
    log "Déploiement des agents MCP..."
    kubectl apply -f k8s/deployments/mcp/

    # Monitoring (léger pour Edge Server)
    log "Déploiement du monitoring..."
    kubectl apply -f k8s/deployments/monitoring/

    # Ingress
    log "Configuration de l'Ingress..."
    kubectl apply -f k8s/ingress/

    success "Déploiement terminé"
}

# Fonction de vérification
verify_deployment() {
    log "Vérification du déploiement..."

    # Vérifier les pods
    kubectl get pods -n twisterlab

    # Vérifier les services
    kubectl get services -n twisterlab

    # Vérifier l'Ingress
    kubectl get ingress -n twisterlab

    # Tests de santé
    log "Tests de santé..."

    # Test API
    if kubectl exec -n twisterlab deployment/twisterlab-api -c api -- curl -f http://localhost:8000/health &>/dev/null; then
        success "API opérationnelle"
    else
        warning "API en cours de démarrage (normal)"
    fi

    success "Vérification terminée"
}

# Fonction de nettoyage
cleanup() {
    log "Nettoyage des ressources temporaires..."
    # Rien à nettoyer pour le moment
}

# Gestion des arguments
case "${1:-}" in
    "install-k3s")
        install_k3s
        ;;
    "prerequisites")
        install_prerequisites
        ;;
    "deploy")
        deploy_optimized
        verify_deployment
        ;;
    "full-deploy")
        install_k3s
        install_prerequisites
        deploy_optimized
        verify_deployment
        success "Déploiement complet terminé sur K3s!"
        ;;
    "destroy")
        kubectl delete namespace twisterlab --ignore-not-found=true
        success "Déploiement détruit"
        ;;
    "status")
        kubectl get all -n twisterlab
        ;;
    "logs")
        component="${2:-api}"
        kubectl logs -n twisterlab -l app=twisterlab,component=$component --tail=50
        ;;
    *)
        echo "Usage: $0 {install-k3s|prerequisites|deploy|full-deploy|destroy|status|logs [component]}"
        echo ""
        echo "Commandes:"
        echo "  install-k3s    - Installer K3s sur Edge Server"
        echo "  prerequisites  - Installer NGINX Ingress et Cert Manager"
        echo "  deploy         - Déployer TwisterLab"
        echo "  full-deploy    - Installation complète K3s + TwisterLab"
        echo "  destroy        - Détruire le déploiement"
        echo "  status         - Status du déploiement"
        echo "  logs [comp]    - Logs d'un composant (api, mcp, monitoring)"
        ;;
esac