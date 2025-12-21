# 🟩 **INSTRUCTIONS COMPLÈTES POUR COPILOT / AGENT VS CODE – PROJET TWISTERLAB (K8S)**

## 1. **But du projet TwisterLab**
TwisterLab est un projet d'infrastructure IA multi-agent cloud-native :
- Architecture : Python 3.x, orchestration sur **Kubernetes** (k3s/minikube/cluster cloud).
- Monitoring, reporting, automation, scrapping, agents autonomes (MCP), orchestration.
- Toute la chaîne est pilotable et observable : Prometheus/Grafana en standard.

***

## 2. **Organisation du dépôt (arborescence cible : prod-ready)**

```
/
├── k8s/                   # Manifests K8s
│   ├── base/              
│   ├── deployments/       
│   ├── monitoring/        
│   └── scripts/           
├── deploy/                # Deployment artifacts
│   ├── docker/            # Dockerfiles (api, mcp-unified, grafana, etc.)
│   └── specs/             # REST API Specs (OpenAPI)
├── src/
│   └── twisterlab/        # Code source prod
├── docs/                  # Guides & Reports
├── demos/                 # Scenarios de démonstration (autonomous_incident.py)
├── archive/               # Legacy/tests obsolètes
├── .github/               # Workflows CI/CD
├── README.md              
└── ...
```

***

## 3. **Actions à effectuer (Copilot/IA/dev)**
**À chaque modif**, s'assurer que :
- Seuls les composants prod (agents functional, API, core, monitoring) restent dans `/src/twisterlab`
- Les tests, démos, scripts legacy, brouillons ou backup sont déplacés dans `/archive` (jamais supprimés sans backup)
- Chaque nouveau microservice ou agent IA doit recevoir :
  - Un fichier de déploiement K8s propre, dans `/k8s/deployments`
  - Un healthcheck K8s (+ readinessProbe si service réseau)
  - Un guide de test minimal dans `/docs` (+ endpoints/test cli au besoin)

***

## 4. **Gestion du monitoring, des métriques et de la sécurité**
- **Monitoring** :
  - Tout nouvel endpoint ou agent exposé log/metrics doit être documenté + branché sur Prometheus (ajout de `scrape_configs` si K8s, ou metrics endpoint `/metrics`)
  - Dashboards à maintenir à jour dans `/k8s/monitoring/grafana` ou `/docs`
- **Sécurité/Secrets** :
  - Aucune info sensible dans le dépôt ! Secrets via K8s manifest `/base/secrets.yaml` uniquement.
  - Toujours gitignore tous les fichiers potentiellement "sensible" (clé privée, db, backup, .env, etc).

***

## 5. **Documentation systématique**
- Le README doit :
  - Expliquer la stack, l'arbo, la philosophie "prod / archive"
  - Lister les étapes de déploiement K8s pour un nouvel utilisateur
  - Pointer vers `/docs/MIGRATION_SWARM_K8S.md` pour contexte infra & CI/CD
  - Documenter la politique de commit/PR ("K8S: ajout agent X", "ARCHIVE: move test X"...)

***

## 6. **Onboarding & évolution**
- **Pour tout nouvel agent/service** :
  - Ajouter la doc d'installation/intégration (Quickstart, manifest .yaml)
  - Écrire une section sur son intégration monitoring (label Prometheus, panel Grafana, healthcheck)
  - Ajouter un exemple "test" facile (curl/kubectl/log)
- **Si upgrade ou migration stack** :
  - Toujours documenter en `/docs` ET par changelog/PR/README
  - Adapter/valider CI/CD dans `.github/workflows`

***

## 7. **Conseils de maintenance & prompts rapides**
- "Nettoie le repo pour ne laisser que le prod dans src/ & les specs K8s dans k8s/"
- "Génère un manifest deployment + service K8s pour le nouvel agent XYZ en prod"
- "Propose un commit message & un plan PR clair pour chaque grosse mouvance"
- "Archive tous les tests qui ne sont pas validés par CI ou pipeline"

***

**Astuce** : Ajoute cette instruction en `/.copilot/instructions.md` ou dans le haut de ton README, et toute génération Copilot/Continue s'alignera sur cette architecture, cette rigueur et cette logique d'évolution "pro/preprod".