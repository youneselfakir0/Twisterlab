#!/bin/bash
set -e

echo "=== Vérification du déploiement ==="

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

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
echo "=== PERSISTENT VOLUMES ==="
kubectl get pv,pvc -n twisterlab

echo ""
echo "Vérification terminée"