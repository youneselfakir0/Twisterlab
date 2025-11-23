# TwisterLab - Makefile
# Commandes communes pour le développement et le déploiement

.PHONY: help install test lint format clean build deploy dev logs

# Variables
PYTHON := python
DOCKER := docker
KUBECTL := kubectl
NAMESPACE := twisterlab

help: ## Afficher cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installer les dépendances Python
	$(PYTHON) -m pip install -e .

test: ## Exécuter les tests
	$(PYTHON) -m pytest tests/ -v --cov=src/twisterlab --cov-report=html

lint: ## Vérifier le code avec les linters
	$(PYTHON) -m ruff check src/twisterlab tests/
	$(PYTHON) -m mypy src/twisterlab

format: ## Formatter le code
	$(PYTHON) -m black src/twisterlab tests/
	$(PYTHON) -m ruff check --fix src/twisterlab tests/

clean: ## Nettoyer les fichiers temporaires
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .pytest_cache/

build: ## Construire l'image Docker
	$(DOCKER) build -t twisterlab:latest .

dev: ## Démarrer l'environnement de développement
	$(DOCKER) compose -f docker-compose.yml up -d

deploy: ## Déployer sur Kubernetes
	$(KUBECTL) apply -f k8s/base/ -n $(NAMESPACE)
	$(KUBECTL) apply -f k8s/apps/ -n $(NAMESPACE)
	$(KUBECTL) apply -f k8s/monitoring/ -n $(NAMESPACE)

logs: ## Afficher les logs des services
	$(KUBECTL) logs -f deployment/twisterlab-api -n $(NAMESPACE)

k8s-deploy: ## Déployer complètement sur K8s
	@echo "🚀 Déploiement TwisterLab sur Kubernetes..."
	$(KUBECTL) apply -f k8s/base/ -n $(NAMESPACE)
	$(KUBECTL) apply -f k8s/apps/ -n $(NAMESPACE)
	$(KUBECTL) apply -f k8s/monitoring/ -n $(NAMESPACE)
	@echo "✅ Déploiement terminé. Vérifiez avec 'make logs'"

k8s-status: ## Vérifier le statut des déploiements K8s
	$(KUBECTL) get pods -n $(NAMESPACE)
	$(KUBECTL) get services -n $(NAMESPACE)
	$(KUBECTL) get ingress -n $(NAMESPACE)