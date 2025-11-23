#!/bin/bash
set -e

echo "=== Installation prérequis ==="

# Installer kubectl si pas déjà installé
if ! command -v kubectl &> /dev/null; then
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
fi

# Vérifier kubectl
kubectl version --client

echo "Prérequis installés"