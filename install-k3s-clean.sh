#!/bin/bash
set -e

echo "=== Installation K3s sur EdgeServer ==="

# Installation K3s sans sudo interactif
curl -sfL https://get.k3s.io | sh -

# Attendre que K3s soit prêt
sleep 30

# Configurer kubectl
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
sudo chmod 644 /etc/rancher/k3s/k3s.yaml

# Vérifier l'installation
kubectl version --client
kubectl cluster-info

echo "K3s installé et configuré"