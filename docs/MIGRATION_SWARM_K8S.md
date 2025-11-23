# 🚀 MIGRATION TWISTERLAB : DOCKER SWARM → KUBERNETES

## 📋 Vue d'ensemble

Ce guide détaille la migration complète de TwisterLab depuis Docker Swarm vers Kubernetes. La migration inclut tous les composants récupérés d'EdgeServer (192.168.0.30) et les adapte pour un déploiement Kubernetes moderne.

## 🎯 Objectifs de la migration

- ✅ **Éliminer Docker Swarm** : Remplacer l'orchestration Swarm par Kubernetes
- ✅ **Résoudre les incompatibilités** : Redis exporter incompatible Swarm + Windows
- ✅ **Architecture cloud-native** : HPA, health checks, secrets management
- ✅ **Maintenir MCP complet** : Tous les agents et intégrations Continue IDE
- ✅ **Monitoring avancé** : Prometheus + Grafana avec auto-scaling

## 📁 Structure des manifests Kubernetes

```
k8s/
├── base/                          # Ressources fondamentales
│   ├── namespace.yaml            # Namespace twisterlab
│   ├── configmap.yaml            # Configuration commune
│   ├── secrets.yaml              # Secrets (mots de passe)
│   └── storage.yaml              # PersistentVolumeClaims
├── deployments/                   # Déploiements des services
│   ├── postgres.yaml             # Base de données PostgreSQL
│   ├── redis.yaml                # Cache Redis
│   ├── api.yaml                  # API FastAPI + HPA
│   └── mcp/                      # Agents MCP
│       ├── orchestrator.yaml     # Agent orchestrateur
│       └── monitoring.yaml       # Agent monitoring
├── monitoring/                    # Stack de monitoring
│   ├── prometheus.yaml           # Métriques + ConfigMap
│   └── grafana.yaml              # Dashboard + PVC
├── ingress/                       # Exposition des services
│   └── main-ingress.yaml         # Routing HTTP/HTTPS
└── scripts/                       # Scripts de déploiement
    ├── deploy-k8s.sh            # Script Bash (Linux)
    └── deploy-k8s.ps1           # Script PowerShell (Windows)
```

## 🏗️ Composants migrés

### Infrastructure
- **PostgreSQL** : StatefulSet avec PVC pour persistance
- **Redis** : Deployment avec health checks (résout le problème Swarm)
- **API TwisterLab** : Deployment avec HPA (2-10 replicas)

### Agents MCP (Model Context Protocol)
- **MCP Orchestrator** : Coordination des agents (port 8080)
- **MCP Monitoring** : Surveillance intelligente (port 8082)
- **Serveur MCP v2.1.0** : Intégration Continue IDE (stdio JSON-RPC)

### Monitoring & Observabilité
- **Prometheus** : Collecte de métriques avec configuration avancée
- **Grafana** : Dashboards avec PVC pour persistance
- **Health checks** : Probes HTTP pour tous les services

### Réseau & Exposition
- **Ingress NGINX** : Routing vers api.twisterlab.local, grafana.twisterlab.local
- **Services ClusterIP** : Communication interne sécurisée
- **TLS** : Configuration Let's Encrypt prête

## 🚀 Déploiement rapide

### Prérequis

1. **Cluster Kubernetes** opérationnel (local: minikube, kind, k3s)
2. **kubectl** configuré et connecté
3. **Docker** pour construire les images
4. **NGINX Ingress Controller** installé:
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
   ```

### Déploiement complet (Windows)

```powershell
# Depuis C:\TwisterLab
cd k8s\scripts
.\deploy-k8s.ps1 -Action deploy
```

### Déploiement complet (Linux/Mac)

```bash
# Depuis /path/to/TwisterLab
cd k8s/scripts
chmod +x deploy-k8s.sh
./deploy-k8s.sh
```

## 🔧 Opérations courantes

### Vérifier le statut
```powershell
.\deploy-k8s.ps1 -Action status
```

### Consulter les logs
```powershell
# Logs API
.\deploy-k8s.ps1 -Action logs -Component api

# Logs MCP
.\deploy-k8s.ps1 -Action logs -Component mcp
```

### Détruire le déploiement
```powershell
.\deploy-k8s.ps1 -Action destroy
```

### Port-forwarding pour développement
```bash
# API locale
kubectl port-forward -n twisterlab svc/twisterlab-api 8000:8000

# Grafana local
kubectl port-forward -n twisterlab svc/grafana 3000:3000
```

## 📊 Services exposés

| Service | URL interne | URL externe | Description |
|---------|-------------|-------------|-------------|
| API | `twisterlab-api.twisterlab.svc.cluster.local:8000` | `api.twisterlab.local` | API FastAPI principale |
| Grafana | `grafana.twisterlab.svc.cluster.local:3000` | `grafana.twisterlab.local` | Dashboard monitoring |
| Prometheus | `prometheus.twisterlab.svc.cluster.local:9090` | `prometheus.twisterlab.local` | Métriques système |
| PostgreSQL | `postgres.twisterlab.svc.cluster.local:5432` | - | Base de données |
| Redis | `redis.twisterlab.svc.cluster.local:6379` | - | Cache distribué |
| MCP Orchestrator | `mcp-orchestrator.twisterlab.svc.cluster.local:8080` | - | Coordination agents |
| MCP Monitoring | `mcp-monitoring.twisterlab.svc.cluster.local:8082` | - | Surveillance système |

## 🤖 Configuration MCP Continue IDE

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

## 🔍 Debugging et monitoring

### Health checks
```bash
# Vérifier tous les pods
kubectl get pods -n twisterlab

# Status détaillé
kubectl describe pod -n twisterlab <pod-name>
```

### Métriques Prometheus
- Accès: http://prometheus.twisterlab.local
- Query: `up{job="twisterlab-api"}`

### Logs structurés
```bash
# Logs avec suivi
kubectl logs -n twisterlab -f deployment/twisterlab-api

# Logs MCP
kubectl logs -n twisterlab -f deployment/mcp-orchestrator
```

## 🔒 Sécurité

### Secrets management
- Mots de passe stockés dans `Secrets` Kubernetes
- Pas de secrets en clair dans les manifests
- Rotation automatique possible

### Réseau
- Services internes en ClusterIP
- Ingress avec TLS obligatoire
- Network policies recommandées (à implémenter)

## 📈 Auto-scaling

### Horizontal Pod Autoscaler (HPA)
- **API**: 2-10 replicas selon CPU (70%) et mémoire (80%)
- **Monitoring**: Ajustable selon les besoins

### Metrics
```bash
kubectl get hpa -n twisterlab
kubectl describe hpa twisterlab-api-hpa -n twisterlab
```

## 🚨 Résolution des problèmes courants

### Pods en CrashLoopBackOff
```bash
kubectl describe pod <pod-name> -n twisterlab
kubectl logs <pod-name> -n twisterlab --previous
```

### Images non trouvées
```bash
# Reconstruire les images
docker build -t twisterlab-api:latest .
kubectl rollout restart deployment/twisterlab-api -n twisterlab
```

### Ingress non accessible
```bash
kubectl get ingress -n twisterlab
kubectl describe ingress twisterlab-ingress -n twisterlab
```

## 🔄 Rollbacks et mises à jour

### Mise à jour d'image
```bash
# Tag nouvelle version
docker build -t twisterlab-api:v2.0 .
docker push twisterlab-api:v2.0

# Mise à jour deployment
kubectl set image deployment/twisterlab-api api=twisterlab-api:v2.0 -n twisterlab
kubectl rollout status deployment/twisterlab-api -n twisterlab
```

### Rollback
```bash
kubectl rollout undo deployment/twisterlab-api -n twisterlab
```

## 📚 Ressources additionnelles

- [Documentation Kubernetes](https://kubernetes.io/docs/)
- [Prometheus Guide](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [MCP Protocol](https://modelcontextprotocol.io/)

## 🎯 Checklist post-déploiement

- [ ] Services accessibles via Ingress
- [ ] MCP intégré dans Continue IDE
- [ ] Métriques collectées dans Prometheus
- [ ] Dashboards Grafana configurés
- [ ] Health checks opérationnels
- [ ] Auto-scaling fonctionnel
- [ ] Backups configurés
- [ ] Monitoring alerts actifs

---

**Migration réalisée le 22 novembre 2025**
**Source**: EdgeServer (192.168.0.30) - Configuration de production
**Destination**: Kubernetes - Architecture cloud-native
**Status**: ✅ Migration complète terminée