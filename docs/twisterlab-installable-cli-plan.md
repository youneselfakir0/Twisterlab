# Plan d'implémentation : TwisterLab Installable CLI & Gateway (v5.2.0)

Ce document présente l'architecture et les étapes d'implémentation pour rendre **TwisterLab** installable de manière transparente sur n'importe quel système (Linux/Windows/macOS), avec un assistant de configuration interactif (`onboard`), un outil de diagnostic de santé (`doctor`), la gestion du serveur en arrière-plan (`gateway`), et l'exécution directe des agents (`agent`), similaire à l'expérience développeur de **OpenClaw**.

---

## 1. Objectifs & Expérience Utilisateur (UX)

L'utilisateur doit pouvoir installer TwisterLab avec une seule commande et interagir avec la plateforme via le terminal :

```bash
# Installation en mode édition (développement local)
pip install -e .

# Initialisation et configuration interactive (Postgres, Redis, LLM, KuCoin)
twisterlab onboard

# Diagnostic rapide de la configuration et de la connectivité
twisterlab doctor

# Lancement et arrêt de l'API / Gateway en arrière-plan (Daemonisé)
twisterlab gateway start
twisterlab gateway status
twisterlab gateway stop

# Exécution d'une mission d'agent directement en ligne de commande
twisterlab agent run maestro "Analyse les sentiments sur BTC-USDT"
```

---

## 2. Architecture de la CLI TwisterLab

La CLI sera écrite en Python à l'aide de la bibliothèque standard `argparse` ou de packages conviviaux comme `click`/`typer` (déjà compatibles avec notre configuration Poetry).

### Structure des modules CLI :
```
src/twisterlab/
├── cli/
│   ├── __init__.py
│   ├── main.py          # Point d'entrée principal (routage des commandes)
│   ├── onboard.py       # Assistant interactif d'onboarding (Génération de .env)
│   ├── doctor.py        # Analyseur de santé (Postgres, Redis, LLM, Exchange, Ingress)
│   ├── gateway.py       # Gestionnaire de daemon Uvicorn (start/stop/status)
│   └── agent.py         # Exécuteur local d'agents (Maestro/Trader/Notion)
```

---

## 3. Détails des Commandes CLI

### 3.1 `twisterlab onboard`
* **Objectif** : Remplacer la configuration manuelle fastidieuse par un assistant interactif.
* **Fonctionnalités** :
  * Demande interactive des informations d'infrastructure (Postgres Host/User/Pass, Redis Host/Port).
  * Demande interactive de l'URL Ollama/Cortex LLM et du modèle par défaut.
  * Demande optionnelle des clés API de KuCoin (Futures Sandbox/Live) et d'Instagram.
  * Génération automatique d'un fichier `.env` ou écriture dans `unified_settings.py`.
  * Sauvegarde des configurations sécurisées dans un fichier de config utilisateur local (ex: `~/.twisterlab/config.json`).

### 3.2 `twisterlab doctor`
* **Objectif** : Valider instantanément l'intégrité de la plateforme.
* **Diagnostics exécutés** :
  * **Database** : Connexion à Postgres, validation des migrations SQLAlchemy (tables `resilience`, `trading`, `archive`).
  * **Cache** : Connexion à Redis, écriture/lecture d'une clé de test.
  * **LLM (Cortex)** : Requête ping/health sur l'API Ollama/Cortex, modèle par défaut disponible.
  * **Exchange** : Appel CCXT public vers KuCoin pour valider le time drift et la connectivité API.
  * **Ports/Sockets** : Vérification de la disponibilité du port `8000`.

### 3.3 `twisterlab gateway`
* **Objectif** : Gérer le cycle de vie du serveur API.
* **Sous-commandes** :
  * `start` : Lance l'instance FastAPI via Uvicorn. Sur Windows, utilise un processus détaché (`subprocess.Popen`); sur Linux/macOS, génère un service systemd ou un processus daemonisé.
  * `status` : Scute la table des processus ou le fichier PID (`~/.twisterlab/gateway.pid`) pour confirmer si le serveur tourne et récupère l'usage CPU/RAM.
  * `stop` : Envoie un signal de fermeture propre (SIGTERM) pour terminer le daemon.

### 3.4 `twisterlab agent`
* **Objectif** : Déclencher et surveiller les missions d'agents locaux ou distants via la CLI.
* **Sous-commandes** :
  * `run <agent_name> <task>` : Démarre l'agent spécifié (ex: maestro, trader, notion) avec la tâche en paramètre.
  * `list` : Liste les agents enregistrés et leurs capacités définies.

---

## 4. Script d'installation universel

Pour imiter le script d'onboarding de OpenClaw, nous allons créer des scripts d'installation en une ligne pour Windows (`install.ps1`) et Linux/macOS (`install.sh`).

### Exemple de flux d'installation :
1. Détecte la version de Python locale (requiert >= 3.11).
2. Crée un environnement virtuel propre `.venv` dans le répertoire d'installation.
3. Installe les dépendances requises via Poetry ou pip (`pip install -e .`).
4. Enregistre l'exécutable `twisterlab` dans le PATH utilisateur.
5. Déclenche immédiatement `twisterlab onboard` pour configurer le système.

---

## 5. Plan de Travail Détaillé

### Étape 1 : Enregistrement de la commande Poetry CLI
Modifier `pyproject.toml` pour lier la commande `twisterlab` au point d'entrée `twisterlab.cli.main:main`.

### Étape 2 : Création de l'Assistant de Configuration (`onboard.py`)
Développer les questions interactives avec validation des entrées utilisateur et la persistance dans un fichier de configuration globale (utilisant `unified_settings`).

### Étape 3 : Implémentation du Diagnostic de Santé (`doctor.py`)
Créer les fonctions de test de socket et de connexion aux bases de données, puis afficher un rapport formaté et coloré dans le terminal.

### Étape 4 : Écriture du Gestionnaire de Processus Daemon (`gateway.py`)
Développer la gestion du fichier PID, le lancement non-bloquant de Uvicorn et la récupération des logs en temps réel.

### Étape 5 : Exécution des Agents (`agent.py`)
Connecter la CLI au registre d'agents (`registry_hybrid.py`) et instancier les agents en temps réel pour exécuter des commandes brutes.

### Étape 6 : Rédaction des Scripts d'Installation Automatisés
Créer `install.ps1` pour Windows et `install.sh` pour Linux.
