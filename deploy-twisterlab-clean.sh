#!/bin/bash
set -e

echo "=== Déploiement TwisterLab ==="

# Aller dans le répertoire des manifests
cd /home/twister/TwisterLab

# Configurer kubectl pour K3s
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Attendre que le cluster soit prêt
kubectl wait --for=condition=Ready node --all --timeout=300s

# Déployer dans l'ordre
echo "Déploiement du namespace..."
kubectl apply -f namespace.yaml

echo "Déploiement des ConfigMaps..."
kubectl apply -f configmap.yaml

echo "Déploiement des Secrets..."
kubectl apply -f secrets.yaml

echo "Déploiement du stockage..."
kubectl apply -f storage.yaml

echo "Déploiement PostgreSQL..."
kubectl apply -f postgres.yaml

echo "Déploiement Redis..."
kubectl apply -f redis.yaml

echo "Déploiement de l'API..."
kubectl apply -f api.yaml

echo "Déploiement de l'orchestrateur..."
kubectl apply -f orchestrator.yaml

echo "Déploiement de Prometheus..."
kubectl apply -f prometheus.yaml

echo "Déploiement de Grafana..."
kubectl apply -f grafana.yaml

echo "Déploiement de l'Ingress..."
kubectl apply -f main-ingress.yaml

echo "Déploiement terminé!"