# 🚀 TwisterLab - Infrastructure IA Multi-Agent Cloud-Native

> **Instructions pour Copilot/Continue** : Consultez [`.copilot/instructions.md`](.copilot/instructions.md) pour comprendre l'organisation, les règles et les bonnes pratiques du projet.

TwisterLab est une infrastructure IA multi-agent cloud-native orchestrée sur **Kubernetes**, incluant monitoring avancé (Prometheus/Grafana), agents autonomes MCP, et une API FastAPI complète.

## 🎯 Vue d'ensemble

- **Architecture** : Python 3.x + Kubernetes (k3s/minikube/cluster cloud)
- **Composants** : API FastAPI, agents MCP, PostgreSQL, Redis, monitoring complet
- **Orchestration** : Déploiement K8s natif avec auto-scaling et health checks
- **Monitoring** : Prometheus + Grafana avec dashboards prédéfinis

## 📁 Organisation du dépôt

```
/
├── k8s/                   # 🏗️ Manifests K8s, scripts de déploiement
│   ├── base/              # Namespace, PVC, secrets/config
│   ├── deployments/       # API, agents, redis, postgres, mcp
│   ├── monitoring/        # Prometheus, Grafana, dashboards
│   ├── ingress/           # Exposition API/grafana (NGINX Ingress)
│   └── scripts/           # Deploy/destroy Bash/PowerShell
├── src/
│   └── twisterlab/        # 🏭 Code source production uniquement
│       ├── api/           # API FastAPI principale
│       ├── agents/        # Agents MCP et logique métier
│       └── core/          # Composants core (twisterlang, etc.)
├── docs/                  # 📚 Guides, tutoriels, migration Swarm→K8s
├── archive/               # 📦 Legacy/tests obsolètes (jamais supprimés)
├── .github/               # 🔄 CI/CD workflows (test, build, deploy)
├── .copilot/              # 🤖 Instructions pour Copilot/Continue
├── pyproject.toml         # ⚙️ Configuration Python (Poetry/pip)
├── .gitignore             # 🚫 Fichiers à ignorer
└── README.md              # 📖 Ce fichier (toujours à jour)
```

### Philosophie "Prod / Archive"
- **`src/twisterlab/`** : **UNIQUEMENT** le code production validé
- **`archive/`** : Tout le reste (tests, démos, legacy) - **jamais supprimé sans backup**
- **Règle** : À chaque modif, nettoyer et archiver ce qui n'est pas prod

## 🚀 Démarrage rapide (Kubernetes)

### Prérequis
- **Kubernetes** opérationnel (k3s, minikube, cluster cloud)
- **kubectl** configuré
- **Docker** pour builder les images
- **NGINX Ingress Controller** :
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
  ```

### Déploiement complet

#### Windows (PowerShell)
```powershell
cd k8s\scripts
.\deploy-k8s.ps1 -Action deploy
```

#### Linux/Mac (Bash)
```bash
cd k8s/scripts
chmod +x deploy-k8s.sh
./deploy-k8s.sh
```

### Vérification du déploiement
```bash
# Status de tous les pods
kubectl get pods -n twisterlab

# Services exposés
kubectl get ingress -n twisterlab
```

## 🌐 Services exposés

| Service | URL externe | Description | Status |
|---------|-------------|-------------|--------|
| **API** | `api.twisterlab.local` | API FastAPI principale | ✅ Prod |
| **Grafana** | `grafana.twisterlab.local` | Dashboards monitoring | ✅ Prod |
| **Prometheus** | `prometheus.twisterlab.local` | Métriques système | ✅ Prod |
| **MCP Orchestrator** | Interne | Coordination agents | ✅ Prod |
| **PostgreSQL** | Interne | Base de données | ✅ Prod |
| **Redis** | Interne | Cache distribué | ✅ Prod |

## 🔧 Opérations courantes

### Monitoring du déploiement
```bash
# Status complet
.\deploy-k8s.ps1 -Action status

# Logs d'un composant
.\deploy-k8s.ps1 -Action logs -Component api
```

### Développement local
```bash
# Port-forwarding API
kubectl port-forward -n twisterlab svc/twisterlab-api 8000:8000

# Port-forwarding Grafana
kubectl port-forward -n twisterlab svc/grafana 3000:3000
```

### Mise à jour d'un service
```bash
# Reconstruire et déployer l'API
docker build -t twisterlab-api:latest -f Dockerfile.api .
kubectl set image deployment/twisterlab-api api=twisterlab-api:latest -n twisterlab
```

### Destruction complète
```bash
.\deploy-k8s.ps1 -Action destroy
```

## 🤖 Intégration MCP + Continue IDE

Après déploiement, configurez VS Code Continue :

```json
{
  "mcpServers": {
    "twisterlab-mcp": {
      "command": "kubectl",
      "args": [
        "exec",
        "-n", "twisterlab",
        "deployment/twisterlab-api",
        "-c", "api",
        "--",
        "python",
        "/app/agents/mcp/mcp_server_continue_sync.py"
      ],
      "env": {
        "PYTHONPATH": "/app",
        "API_URL": "http://twisterlab-api.twisterlab.svc.cluster.local:8000"
      }
    }
  }
}
```

## 📊 Monitoring & Observabilité

- **Prometheus** : Métriques automatiques sur tous les services
- **Grafana** : Dashboards prédéfinis pour API, agents, infrastructure
- **Health checks** : Probes K8s sur tous les déploiements
- **Auto-scaling** : HPA sur l'API (2-10 replicas selon CPU/mémoire)

### Accès aux métriques
```bash
# Dashboard Grafana
open http://grafana.twisterlab.local

# Interface Prometheus
open http://prometheus.twisterlab.local
```

## 🔒 Sécurité & Secrets

- **Aucune donnée sensible** dans le dépôt
- **Secrets K8s** : Tous les mots de passe dans `/k8s/base/secrets.yaml`
- **Gitignore strict** : Clés privées, backups, .env automatiquement ignorés

## 📚 Documentation

- **[Guide de migration Swarm→K8s](docs/MIGRATION_SWARM_K8S.md)** : Contexte infrastructure
- **[Instructions Copilot](.copilot/instructions.md)** : Règles pour IA/dev
- **[Architecture V2](docs/ARCHITECTURE_V2_VISION.md)** : Vision technique complète
- **[Onboarding](docs/ONBOARDING.md)** : Guide pour nouveaux contributeurs

## 🚨 Troubleshooting

### Pods en CrashLoopBackOff
```bash
kubectl describe pod <pod-name> -n twisterlab
kubectl logs <pod-name> -n twisterlab --previous
```

### Images non trouvées
```bash
# Reconstruire les images
docker build -t twisterlab-api:latest -f Dockerfile.api .
kubectl rollout restart deployment/twisterlab-api -n twisterlab
```

### Ingress inaccessible
```bash
kubectl get ingress -n twisterlab
kubectl describe ingress twisterlab-ingress -n twisterlab
```

## 🔄 Évolution du projet

### Pour ajouter un nouvel agent/service :
1. Code dans `src/twisterlab/agents/`
2. Manifest K8s dans `k8s/deployments/`
3. Healthcheck + readinessProbe
4. Documentation dans `docs/`
5. Intégration monitoring (Prometheus + Grafana)

### Politique de commits :
- `"K8S: ajout agent X"` - Nouvelles fonctionnalités
- `"ARCHIVE: move test X"` - Nettoyage/refactoring
- `"DOCS: update guide Y"` - Documentation
- `"FIX: resolve issue Z"` - Corrections

## 🤝 Contribution

1. Lire les [instructions Copilot](.copilot/instructions.md)
2. Respecter l'arborescence prod/archive
3. Tester sur K8s avant commit
4. Documenter les changements

---

**Migration Swarm→K8s terminée le 22 novembre 2025** | **Status** : ✅ Production-ready
