#!/bin/bash
set -e

echo "=== Installation Local Path Provisioner ==="

# Installer local-path provisioner pour le stockage local
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.24/deploy/local-path-storage.yaml

# Attendre que le provisioner soit prêt
kubectl wait --for=condition=available --timeout=300s deployment/local-path-provisioner -n local-path-storage

# Définir local-path comme storage class par défaut
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

echo "Local Path Provisioner installé"