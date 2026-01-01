# TwisterLab MCP - Guide de Configuration & Restauration

## Vue d'ensemble

TwisterLab v3.3.0 est un serveur MCP (Model Context Protocol) "Unifié" qui agit comme une passerelle entre vos LLMs (Claude, Ollama) et votre infrastructure Kubernetes. Il orchestre des agents autonomes (Browser, Monitoring, System).

## Architecture du Système

### Composants Principaux

1. **Serveur MCP Unifié (Python)** - Hub central basé sur FastAPI (`src/twisterlab/api/main.py`).
2. **Ollama (Remote)** - Runtime LLM (`192.168.0.20`).
3. **Cluster Kubernetes** (`192.168.0.30`):
   - **Redis** (Cache distribué & Rate Limiting)
   - **PostgreSQL** (Persistance & Logs)
   - **Prometheus/Grafana** (Métriques & Observabilité)
   - **Playwright** (Navigation Web sans tête)

### Modes de Transport MCP

Le système supporte deux modes de connexion simultanés :
1. **STDIO (Mode Pro)** : Via `kubectl exec` ou `docker exec` (Recommendé pour Claude Desktop & Continue).
2. **SSE (HTTP)** : Via Server-Sent Events sur `/api/v1/mcp/sse` (Pour clients distants).

---

## Configuration MCP (Client)

### 1. Claude Desktop (Windows/Mac)

C'est la méthode la plus robuste ("Pro"), encapsulée dans le container Docker de production.

**Fichier**: `%APPDATA%\Claude\claude_desktop_config.json` (Windows) ou `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac).

```json
{
  "mcpServers": {
    "TwisterLab Pro": {
      "command": "kubectl",
      "args": [
        "exec",
        "-i",
        "-n",
        "twisterlab",
        "deployment/twisterlab-api",
        "--",
        "python",
        "-m",
        "twisterlab.agents.mcp.server"
      ],
      "env": {
        "PYTHONPATH": "/app/src"
      }
    }
  }
}
```

### 2. Continue IDE / VS Code

Configuration dans `~/.continue/config.json`.

```json
{
  "name": "TwisterLab",
  "type": "command",
  "command": "kubectl exec -i -n twisterlab deployment/twisterlab-api -- python -m twisterlab.agents.mcp.server"
}
```

---

## Installation et Démarrage (Serveur)

### Prérequis

- **Python 3.11+**
- **Docker & Kubernetes**
- **Ollama** (accessible sur le réseau)

### Déploiement Production (K8s)

Le déploiement est automatisé via GitHub Actions, mais peut être forcé manuellement :

```bash
# Appliquer les manifestes
kubectl apply -f k8s/core/
kubectl apply -f k8s/api/

# Forcer le redémarrage pour mise à jour
kubectl rollout restart deployment twisterlab-api -n twisterlab
```

### Démarrage Local (Dev)

Pour tester sans Kubernetes :

```powershell
# Installer les dépendances
pip install poetry
poetry install

# Lancer le serveur API (avec support SSE local)
$env:PYTHONPATH="src"; python -m uvicorn twisterlab.api.main:app --port 8000 --reload
```

---

## Fonctionnalités & Outils Disponibles

### 1. Agent Web (Browser)
*Basé sur Playwright.*
- **Outil MCP** : `browse_web`
- **Capacités** : Navigation réelle, extraction de texte, captures d'écran (base64).
- **Exemple Claude** : *"Va sur google.com et fais une capture d'écran."*

### 2. Surveillance Système
*Basé sur psutil & Docker SDK.*
- **Outil MCP** : `monitor_system`
- **Capacités** : CPU, RAM, Disk, santé des conteneurs K8s.
- **Exemple Claude** : *"Fais un check up complet du système."*

### 3. Base de Données & Cache
- **PostgreSQL** : Stockage des logs d'audit et tâches.
- **Redis** : Cache rapide pour les réponses des agents.

---

## Dépannage

### Claude affiche "Could not load app settings"
Cela signifie généralement que la commande `kubectl` échoue ou est introuvable.

1. Vérifiez que `kubectl` fonctionne dans votre terminal :
   ```bash
   kubectl get pods -n twisterlab
   ```
2. Vérifiez le chemin absolu de kubectl si nécessaire dans la config JSON.

### L'Agent Browser ne fonctionne pas
Si vous avez l'erreur "Browser executables not found" :
```bash
# Vérifier l'installation dans le pod
kubectl exec -it -n twisterlab deployment/twisterlab-api -- playwright install chromium
```
*(Note: Ceci est normalement géré par le Dockerfile)*

### Vérification des Logs
```bash
# Logs du serveur API
kubectl logs -f -n twisterlab deployment/twisterlab-api

# Logs MCP spécifiques (via STDIO)
# Ils sont redirigés vers stderr, donc visibles dans les logs du pod.
```

## Backup et Maintenance

### Sauvegarde BDD
```bash
kubectl exec -n twisterlab postgres-0 -- pg_dump -U twisterlab db_twisterlab > backup_v3.sql
```

### Reset Rapide du Cache
```bash
kubectl exec -n twisterlab redis-pod-name -- redis-cli FLUSHALL
```

---

**TwisterLab v3.3.0** - *Release Candidate Stable*
