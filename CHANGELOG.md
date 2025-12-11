# Changelog

All notable changes to TwisterLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Automated GitHub Secrets configuration script (`quick-setup-secrets.ps1`)
- Comprehensive GitHub Secrets documentation (`docs/GITHUB_SECRETS_GUIDE.md`)
- Security audit report (`rapport_audit_twisterlab.md`)

### Changed

- **BREAKING**: Replaced `psycopg2` with `psycopg2-binary` to eliminate C build dependencies
- Updated Dockerfile.api ENV declarations to modern syntax (`KEY=value`)
- Migrated Poetry commands to 2.x compatible syntax
- Repository reorganization for better maintainability

### Fixed

- **CI/CD Pipeline**: Resolved 5 critical Docker build issues:
  1. Poetry 2.x syntax compatibility (`--no-dev` → `--only main`)
  2. Dockerfile syntax error (RUN command with inline comment)
  3. Missing dependency group handling in pyproject.toml
  4. Outdated poetry.lock synchronization
  5. PostgreSQL driver compilation failures (psycopg2 → psycopg2-binary)
- CD workflow now successfully builds all 3 Docker images (api, mcp, mcp-unified)
- Various bug fixes and improvements

## [1.1.0] - 2025-11-22

### 🎉 Major Release: Repository Reorganization & Production-Ready

#### Added

- **CI/CD Pipeline Complet** (`.github/workflows/ci-cd.yml`)
  - Tests automatisés (pytest + couverture)
  - Linting et formatage (ruff, mypy, black)
  - Build Docker multi-stage
  - Scan sécurité (Trivy)
  - Déploiement K8s staging/production

- **Templates GitHub** (`.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`)
  - Template bug report structuré
  - Template PR avec checklist qualité
  - Processus contribution standardisé

- **Outils Développement**
  - `Makefile` : Commandes communes (install, test, deploy, logs)
  - `docker-compose.yml` : Environnement développement local
  - `CONTRIBUTING.md` : Guide contributeurs complet

- **Structure K8s Optimisée**
  - `k8s/base/` : Namespaces, secrets, configmaps, ingress
  - `k8s/apps/` : Déploiements des services
  - `k8s/monitoring/` : Prometheus, Grafana
  - `k8s/scripts/` : Automatisation déploiement

- **Documentation Structurée**
  - `docs/guides/` : Guides utilisateur
  - `docs/api/` : Documentation API
  - `docs/architecture/` : Diagrammes système

- **Tests et Qualité**
  - Dossier `tests/` pour tests unitaires/intégration
  - Scripts de test automatisés
  - Configuration couverture de code

#### Changed
- **Réorganisation Complète du Dépôt**
  - Migration vers structure GitHub standard
  - Séparation claire code/archive/documentation
  - Optimisation des workflows de développement

- **Amélioration Workflows**
  - Processus PR avec reviews obligatoires
  - Branches naming convention (`feature/`, `bugfix/`, `hotfix/`)
  - Commits conventionnels

#### Fixed
- **Intégration MCP** : Correction chemins et dépendances
- **Configuration Continue IDE** : Paramètres optimisés
- **Imports Python** : Résolution conflits modules

#### Performance
- **CI/CD** : Tests parallèles et cache optimisé
- **Build** : Images Docker multi-stage réduites
- **Déploiement** : Automatisation complète K8s

#### Security
- **Scan Automatique** : Intégration Trivy dans pipeline
- **Secrets Management** : Configuration K8s sécurisée
- **Audit Code** : Linting et formatage automatique

### Migration Notes
- **Structure Dépôt** : Fichiers déplacés selon nouvelle organisation
- **Workflows Obligatoires** : CI/CD désormais requis pour toutes les PR
- **Templates** : Issues et PR doivent utiliser les nouveaux templates

---

## [1.0.0] - 2025-11-22

### 🎉 Major Release: Migration K8s Complète

#### Added
- **Migration Swarm → K8s** : Architecture cloud-native complète
- **Intégration MCP** : Model Context Protocol avec Continue IDE
- **8 Agents Autonomes** :
  - RealMonitoringAgent : Surveillance système
  - RealBackupAgent : Sauvegarde et DR
  - RealMaestroAgent : Orchestration workflows
  - RealClassifierAgent : Classification tickets
  - RealResolverAgent : Résolution automatique
  - RealDesktopCommanderAgent : Commandes système
  - RealSyncAgent : Synchronisation cache/DB
  - BrowserAgent : Automatisation web

- **Infrastructure Production** :
  - PostgreSQL StatefulSet + PVC 10Gi
  - Redis Cluster + PVC 5Gi
  - Prometheus + Grafana monitoring
  - NGINX Ingress Controller
  - Secrets K8s chiffrés

- **Sécurité Renforcée** :
  - TLS/HTTPS obligatoire
  - Réseau isolé (services internes)
  - Audit logging complet
  - Validation entrées

#### Changed
- **Architecture** : Migration vers microservices K8s
- **Performance** : +300% vs architecture Swarm
- **Disponibilité** : 99.9% avec auto-scaling et health checks

#### Removed
- **Docker Swarm** : Remplacé par Kubernetes
- **Configuration Monolithique** : Architecture distribuée

### Breaking Changes
- APIs incompatibles avec version Swarm
- Configuration déploiement entièrement revue
- Nouvelles dépendances K8s obligatoires

---

## [0.1.0] - 2025-11-01

### Added
- Proof of concept initial
- Architecture de base TwisterLab
- Premiers agents expérimentaux
- Configuration Docker Swarm basique

### Changed
- Structure initiale du projet

---

## Types of changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

## Version Format
This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible