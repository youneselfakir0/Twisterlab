#!/bin/bash
set -e

echo "=== Configuration sudo sans mot de passe ==="

# Ajouter l'utilisateur au groupe sudo et configurer sudo sans mot de passe
echo 'twister ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/twister

echo "Configuration sudo terminée"