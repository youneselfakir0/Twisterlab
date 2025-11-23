# 🚀 Guide d'Onboarding - TwisterLab K8s

Bienvenue dans TwisterLab ! Ce guide vous aidera à comprendre et contribuer au projet d'infrastructure IA multi-agent cloud-native.

## 🎯 Vue d'ensemble du projet

TwisterLab est une plateforme d'orchestration d'agents IA avec :

- **API FastAPI** pour l'exposition des services
- **Agents MCP** (Model Context Protocol) pour l'intégration IDE
- **Monitoring complet** avec Prometheus + Grafana
- **Architecture K8s-native** avec auto-scaling et health checks

## 📋 Checklist d'onboarding

### 1. Configuration de l'environnement

- [ ] Installer Kubernetes (k3s/minikube)
- [ ] Installer kubectl
- [ ] Installer Docker
- [ ] Cloner le repository

### 2. Compréhension de l'architecture

- [ ] Lire le [README principal](../README.md)
- [ ] Lire les [instructions Copilot](../.copilot/instructions.md)
- [ ] Lire le [guide de migration Swarm→K8s](MIGRATION_SWARM_K8S.md)
- [ ] Explorer la structure `k8s/` et `src/twisterlab/`

### 3. Premier déploiement

- [ ] Installer NGINX Ingress Controller
- [ ] Lancer `./k8s/scripts/deploy-k8s.sh` (Linux/Mac) ou `.\k8s\scripts\deploy-k8s.ps1` (Windows)
- [ ] Vérifier que tous les pods sont `Running`
- [ ] Tester l'accès aux services via Ingress

### 4. Développement et contribution

- [ ] Comprendre la philosophie "prod/archive"
- [ ] Configurer Continue IDE avec MCP
- [ ] Tester les modifications localement
- [ ] Respecter les conventions de commit

## 🏗️ Comment contribuer

### Ajout d'un nouvel agent

1. **Code** : Placer dans `src/twisterlab/agents/`
2. **K8s** : Créer manifest dans `k8s/deployments/`
3. **Monitoring** : Ajouter healthcheck + métriques Prometheus
4. **Docs** : Documenter dans `docs/`

### Modification existante

1. **Toujours** nettoyer : déplacer legacy vers `archive/`
2. **Tester** sur K8s avant commit
3. **Documenter** les changements
4. **Suivre** les conventions de commit

## 🔧 Commandes essentielles

```bash
# Status du déploiement
kubectl get pods -n twisterlab
kubectl get ingress -n twisterlab

# Logs d'un service
kubectl logs -n twisterlab deployment/twisterlab-api

# Port-forwarding pour dev
kubectl port-forward -n twisterlab svc/twisterlab-api 8000:8000

# Mise à jour d'image
kubectl set image deployment/<name> <container>=<image> -n twisterlab
```

## 📚 Ressources importantes

- **[Instructions Copilot](../.copilot/instructions.md)** : Règles et bonnes pratiques
- **[Guide de migration](MIGRATION_SWARM_K8S.md)** : Contexte technique
- **[Architecture V2](../docs/architecture/ARCHITECTURE_V2_VISION.md)** : Vision complète
- **Issues GitHub** : Pour questions spécifiques

## 🚨 Points d'attention

- **Jamais** de secrets dans le code
- **Toujours** archiver avant de supprimer
- **Tester** sur K8s avant merge
- **Documenter** les changements d'architecture

## 💬 Support

- **Issues GitHub** : Pour bugs et features
- **Documentation** : Vérifier `docs/` d'abord
- **Instructions Copilot** : Pour guidance IA/dev

---

**Dernière mise à jour** : Novembre 2025