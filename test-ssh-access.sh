#!/bin/bash

# Script de test d'accès SSH au conteneur EdgeServer
# Usage: ./test-ssh-access.sh [container_name]

CONTAINER_NAME="${1:-twisterlab_api}"
SSH_PORT="${2:-2222}"
SSH_USER="${3:-twisterlab}"

echo "🔍 Test d'accès SSH au conteneur EdgeServer"
echo "=========================================="
echo "Conteneur: $CONTAINER_NAME"
echo "Port SSH: $SSH_PORT"
echo "Utilisateur: $SSH_USER"
echo ""

# Vérifier si le conteneur existe
if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Conteneur '$CONTAINER_NAME' non trouvé ou non démarré"
    echo ""
    echo "📋 Conteneurs disponibles:"
    docker ps --format "table {{.Names}}\t{{.Ports}}"
    exit 1
fi

echo "✅ Conteneur trouvé"

# Tester la connectivité réseau
echo ""
echo "🌐 Test de connectivité réseau..."
if docker exec "$CONTAINER_NAME" nc -z localhost 22 2>/dev/null; then
    echo "✅ Port SSH (22) ouvert dans le conteneur"
else
    echo "❌ Port SSH (22) fermé dans le conteneur"
fi

# Vérifier si SSH est en cours d'exécution
echo ""
echo "🔧 Vérification du service SSH..."
SSH_STATUS=$(docker exec "$CONTAINER_NAME" ps aux | grep sshd | grep -v grep)
if [ -n "$SSH_STATUS" ]; then
    echo "✅ Service SSH en cours d'exécution:"
    echo "$SSH_STATUS"
else
    echo "❌ Service SSH non trouvé"
fi

# Tester l'accès direct au conteneur
echo ""
echo "🐳 Test d'accès direct au conteneur..."
echo "Commande: docker exec -it $CONTAINER_NAME /bin/bash"
echo "Si SSH ne fonctionne pas, utilisez cette commande pour déboguer"

# Informations de connexion
CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER_NAME")
HOST_PORT=$(docker port "$CONTAINER_NAME" 22/tcp | cut -d: -f2)

echo ""
echo "📋 Informations de connexion SSH:"
echo "  Adresse IP du conteneur: $CONTAINER_IP"
echo "  Port exposé sur l'hôte: $HOST_PORT"
echo ""
echo "🔑 Utilisateurs disponibles:"
echo "  root: twisterlab_root_2024!"
echo "  twisterlab: twisterlab_ssh_2024!"
echo "  app: twisterlab_app_2024!"
echo ""
echo "💡 Commandes de test:"
echo "  ssh -p $HOST_PORT root@localhost"
echo "  ssh -p $HOST_PORT twisterlab@localhost"
echo "  ssh -p $HOST_PORT app@localhost"
echo ""
echo "⚠️  Note: Utilisez des clés SSH en production au lieu des mots de passe!"

# Test de connexion rapide (si SSH est disponible)
echo ""
echo "🔗 Test de connexion SSH rapide..."
if command -v ssh >/dev/null 2>&1; then
    echo "Tentative de connexion SSH (timeout 5s)..."
    timeout 5 ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -p "$HOST_PORT" "$SSH_USER"@localhost "echo 'SSH connection successful'" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Connexion SSH réussie"
    else
        echo "❌ Échec de la connexion SSH"
        echo "   Vérifiez les logs du conteneur: docker logs $CONTAINER_NAME"
    fi
else
    echo "⚠️  Client SSH non trouvé sur l'hôte"
fi

echo ""
echo "📝 Logs du conteneur (dernières lignes):"
docker logs "$CONTAINER_NAME" 2>&1 | tail -10