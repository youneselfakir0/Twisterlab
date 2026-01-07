# 🌀 INSTRUCTIONS COPILOT - TWISTERLAB : PLATEFORME IA AUTONOME POUR SUPPORT TECHNIQUE

## 🎯 VISION DU PROJET (À TOUJOURS GARDER EN TÊTE)

**TwisterLab résout QUOI ?**
→ Automatisation complète du support technique via agents IA autonomes
→ Les agents analysent, diagnostiquent, recherchent des solutions et les appliquent
→ Prévention proactive des incidents avant qu'ils n'arrivent
→ Destiné aux PME et entreprises qui veulent un support technique 24/7 intelligent

**Architecture Conceptuelle - Le Cerveau et Ses Agents**
```
[TICKET CLIENT] → "Base de données lente depuis ce matin"
         ↓
    🧠 MAESTRO (Cerveau orchestrateur - LLM)
         │
         ├─ Analyse le problème avec contexte
         ├─ Décide de la stratégie d'intervention
         ├─ Dispatche aux agents appropriés
         │
         ├──→ 😊 SentimentAnalyzer    → Détecte urgence (client en colère?)
         ├──→ 🏷️  Classifier          → Catégorise (DATABASE/NETWORK/APP)
         ├──→ 📊 MonitoringAgent      → Collecte métriques serveur
         ├──→ 🌐 BrowserAgent         → Recherche solutions sur web/docs
         ├──→ 💻 DesktopCommander     → Exécute commandes système
         ├──→ 💾 BackupAgent          → Backup avant intervention
         └──→ ✅ ResolverAgent        → Applique solution + log résultat
         ↓
    [TICKET RÉSOLU] + Monitoring continue pour prévenir récidive
```

**9 Agents Actuels** (tous dans `src/twisterlab/agents/real/`)
1. **RealMaestroAgent** - Orchestrateur intelligent (cerveau)
2. **SentimentAnalyzerAgent** - Analyse urgence/émotion ticket
3. **RealClassifierAgent** - Catégorise les problèmes
4. **RealMonitoringAgent** - Surveille santé système
5. **RealBrowserAgent** - Recherche solutions sur web (Playwright)
6. **RealDesktopCommanderAgent** - Exécute commandes/scripts
7. **RealResolverAgent** - Applique solutions et marque résolu
8. **RealBackupAgent** - Sécurise données avant intervention
9. **RealSyncAgent** - Synchronise données entre systèmes

---

## 🏗️ ARCHITECTURE TECHNIQUE

### Stack Technologique
- **Backend**: Python 3.11+ avec FastAPI (async)
- **Agents**: Architecture multi-classe (TwisterAgent, BaseAgent, CoreAgent)
- **Database**: PostgreSQL avec SQLAlchemy async (`asyncpg`)
- **Cache**: Redis pour performance
- **LLM**: Intégration Ollama/Claude via MCP (Model Context Protocol)
- **Browser Automation**: Playwright (Chromium headless)
- **Orchestration**: Kubernetes (K8s) avec deployments/services/HPA
- **Monitoring**: Prometheus + Grafana + métriques custom
- **CI/CD**: GitHub Actions avec tests automatisés

### Hiérarchie des Classes d'Agents
```python
# 3 classes de base possibles selon le besoin:

1. TwisterAgent (src/twisterlab/agents/base.py)
   - Multi-framework (Microsoft/LangChain/OpenAI)
   - Pour agents nécessitant export schema
   
2. BaseAgent (src/twisterlab/agents/base/base_agent.py)
   - Simple avec méthode _process()
   - Pour agents basiques
   
3. CoreAgent (src/twisterlab/agents/core/base.py)
   - Capability-based avec AgentCapability
   - Pour agents MCP avec déclarations explicites
```

### Points Critiques Techniques

**❌ ERREUR FATALE - Database**
```python
# ❌ JAMAIS ÇA - Crash l'app
from sqlalchemy import create_engine
DATABASE_URL = "postgresql://..."

# ✅ TOUJOURS async
from sqlalchemy.ext.asyncio import create_async_engine
DATABASE_URL = "postgresql+asyncpg://..."  # ou sqlite+aiosqlite://
```

**✅ Patterns à Suivre**
```python
# Sessions DB async
from twisterlab.database.session import AsyncSessionLocal, get_db

# Pydantic v2 (pas v1!)
model.model_dump()  # ✅
model.dict()        # ❌

# Tests avec markers
@pytest.mark.asyncio
@pytest.mark.unit  # ou integration, e2e
async def test_something(): ...

# Agent lookup forgiving
registry.get_agent("classifier")            # ✅
registry.get_agent("real-classifier")       # ✅
registry.get_agent("RealClassifierAgent")   # ✅
```

---

## 📁 STRUCTURE DU PROJET

```
twisterlab/
├── src/twisterlab/              # CODE PRODUCTION UNIQUEMENT
│   ├── agents/
│   │   ├── real/                # 9 agents autonomes
│   │   ├── core/                # Classes de base
│   │   ├── mcp/                 # Serveur MCP
│   │   └── registry.py          # Singleton registry
│   ├── api/
│   │   ├── main.py              # FastAPI app
│   │   └── routes_mcp_real.py   # 39+ endpoints MCP
│   └── database/
│       └── session.py           # Async sessions
│
├── tests/                       # Tests organisés par type
│   ├── unit/                    # Tests isolés rapides
│   ├── integration/             # Tests multi-composants
│   └── e2e/                     # Tests Playwright
│
├── k8s/                         # Manifests Kubernetes
│   ├── base/                    # ConfigMaps, Secrets
│   ├── deployments/             # Deployments par service
│   └── monitoring/              # Prometheus/Grafana
│
├── deploy/
│   ├── docker/                  # Dockerfiles optimisés (265MB)
│   └── specs/                   # OpenAPI specs
│
├── docs/                        # Documentation complète
│   ├── agents/                  # Guide par agent
│   ├── architecture/            # Diagrammes et design
│   └── OPERATIONS/              # Guides opérationnels
│
├── archive/                     # CODE LEGACY (ne pas toucher)
│   ├── legacy_tests/
│   └── old_implementations/
│
├── scripts/                     # Scripts DevOps
│   ├── new_agent_scaffold.py    # Créer nouvel agent
│   └── twisterlab-health.ps1    # Vérification santé
│
├── .github/workflows/           # CI/CD automatique
├── docker-compose.yml           # Stack local complète
└── pyproject.toml               # Dependencies Poetry
```

---

## 🚀 COMMANDES ESSENTIELLES

### Développement Local
```bash
# Lancer l'API
uvicorn src.twisterlab.api.main:app --reload --port 8000

# Tests par catégorie
pytest tests/unit -v                    # Tests unitaires rapides
pytest tests/integration -v             # Tests intégration
$env:E2E='1'; pytest -m e2e -v         # E2E avec Playwright

# Linting (obligatoire avant commit)
ruff check src tests
black src tests

# Docker stack complète
docker-compose up -d                    # Tout (postgres+redis+api+mcp+grafana)
docker-compose logs -f api              # Voir logs API
```

### Kubernetes
```bash
# Déployer sur K8s
kubectl apply -f k8s/base/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/monitoring/

# Vérifier santé
kubectl get pods -n twisterlab
kubectl logs -f deployment/twisterlab-api -n twisterlab

# Tester endpoint
curl http://localhost:30000/health
```

---

## 🎓 GUIDE POUR AJOUTER UN NOUVEL AGENT

### 1. Scaffolding
```bash
python scripts/new_agent_scaffold.py --name PredictiveAgent
```

### 2. Implémenter l'Agent
```python
# src/twisterlab/agents/real/predictive_agent.py
from twisterlab.agents.core.base import (
    TwisterAgent, 
    AgentCapability, 
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType
)

class PredictiveAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "predictive"
    
    @property
    def description(self) -> str:
        return "Predicts system failures before they occur using ML"
    
    def get_capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="predict_failure",
                description="Analyze metrics and predict potential failures",
                handler="handle_predict",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "metrics_data", 
                        ParamType.OBJECT, 
                        "Historical metrics to analyze",
                        required=True
                    )
                ]
            )
        ]
    
    async def handle_predict(self, metrics_data: dict) -> AgentResponse:
        # Logique de prédiction ML ici
        risk_score = self._analyze_patterns(metrics_data)
        
        return AgentResponse(
            success=True, 
            data={
                "risk_score": risk_score,
                "predicted_failure": risk_score > 0.7,
                "recommendation": "Scale up resources" if risk_score > 0.7 else "All good"
            }
        )
```

### 3. Enregistrer dans Registry
```python
# src/twisterlab/agents/registry.py
from twisterlab.agents.real.predictive_agent import PredictiveAgent

class AgentRegistry:
    def initialize_agents(self):
        # ... autres agents ...
        predictive = PredictiveAgent()
        
        self._agents = {
            # ... autres ...
            predictive.name.lower(): predictive,
        }
```

### 4. Ajouter Endpoint MCP
```python
# src/twisterlab/api/routes_mcp_real.py
@router.post("/predict_failure")
async def predict_failure(request: PredictRequest):
    agent = agent_registry.get_agent("predictive")
    result = await agent.handle_predict(request.metrics_data)
    return MCPResponse(status="ok" if result.success else "error", data=result.data)
```

### 5. Tests
```python
# tests/unit/test_predictive_agent.py
import pytest
from twisterlab.agents.real.predictive_agent import PredictiveAgent

@pytest.mark.asyncio
@pytest.mark.unit
async def test_predict_low_risk():
    agent = PredictiveAgent()
    result = await agent.handle_predict({"cpu": 30, "memory": 40})
    
    assert result.success is True
    assert result.data["risk_score"] < 0.5
    assert result.data["predicted_failure"] is False
```

---

## 🎯 OBJECTIFS PRIORITAIRES ACTUELS

### 🔴 CRITIQUE - À Faire Maintenant
1. **Implémenter RealMaestroAgent complet**
   - Intégration LLM (Ollama local ou Claude via MCP)
   - Logique de dispatch intelligente aux autres agents
   - Gestion du contexte et mémoire de conversation
   
2. **Créer Démo End-to-End**
   - Scénario: "Database lente" → Résolution auto complète
   - Script: `demos/ticket_resolution_demo.py`
   - Vidéo/Screenshots pour portfolio

3. **Documentation Visuelle**
   - Diagrammes d'architecture (C4 model)
   - Flow de résolution de ticket (sequence diagram)
   - README avec GIFs/vidéos du système en action

### 🟡 IMPORTANT - Semaine Prochaine
4. **Agent Prédictif ML**
   - Analyse patterns historiques
   - Prédiction pannes avant incident
   - Alertes proactives

5. **Dashboard Grafana Custom**
   - Métriques par agent
   - Taux de résolution automatique
   - Performance globale système

### 🟢 NICE TO HAVE - Plus Tard
6. Tests E2E automatisés complets
7. Multi-tenancy (isolation par client)
8. Interface web React pour visualisation

---

## 🛡️ RÈGLES DE SÉCURITÉ

### Secrets & Données Sensibles
```bash
# ❌ JAMAIS commit ces fichiers
.env
*.key
*.pem
secrets.yaml (non-template)
database backups

# ✅ Toujours utiliser
.env.example (template)
k8s/base/secrets.yaml (avec placeholders)
GitHub Secrets pour CI/CD
```

### Variables d'Environnement Critiques
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # Async obligatoire!
REDIS_URL=redis://host:6379/0
SECRET_KEY=<généré aléatoire>
OLLAMA_BASE_URL=http://localhost:11434              # LLM local
RATE_LIMIT_PER_MINUTE=60
PYTHONPATH=src
```

---

## 📊 MONITORING & MÉTRIQUES

### Endpoints Importants
- `/health` - Santé globale API
- `/metrics` - Métriques Prometheus
- `/docs` - Documentation Swagger auto-générée
- `/v1/mcp/tools/list_autonomous_agents` - Liste agents actifs

### Métriques Custom par Agent
```python
from prometheus_client import Counter, Histogram

# Exemple pour SentimentAnalyzer
sentiment_total = Counter(
    'sentiment_analysis_total',
    'Total sentiment analyses',
    ['sentiment', 'language']
)

sentiment_confidence = Histogram(
    'sentiment_confidence_score',
    'Confidence score distribution',
    buckets=[0.0, 0.5, 0.7, 0.9, 1.0]
)
```

---

## 💡 CONSEILS POUR COPILOT

### Quand Générer du Code
- **Toujours demander confirmation** avant modifications majeures
- **Expliquer les choix** d'architecture/patterns
- **Proposer alternatives** quand plusieurs approches possibles
- **Inclure tests** avec tout nouveau code
- **Documenter** les fonctions complexes

### Patterns à Privilégier
```python
# ✅ Async partout
async def fetch_data(): ...

# ✅ Type hints stricts
def process(data: dict[str, Any]) -> AgentResponse: ...

# ✅ Error handling explicite
try:
    result = await agent.execute()
except Exception as e:
    logger.error(f"Agent failed: {e}")
    return AgentResponse(success=False, error=str(e))

# ✅ Logging informatif
logger.info(f"🚀 Agent {self.name} starting task: {task_id}")
logger.debug(f"Input params: {params}")
```

### Questions à Poser Avant de Coder
1. "Est-ce aligné avec la vision du projet (support technique automatisé)?"
2. "Cet agent/feature aide vraiment à résoudre des tickets?"
3. "La complexité est-elle justifiée?"
4. "Y a-t-il déjà un agent qui fait ça?"
5. "Peut-on réutiliser du code existant?"

---

## 🎬 EXEMPLE CONCRET - Scénario Complet

**Ticket**: "Notre application web ne répond plus depuis 10 minutes"

```python
# 1. Sentiment urgence critique détectée
sentiment_result = await sentiment_agent.analyze("ne répond plus depuis 10 minutes")
# → urgence=HIGH, mots_clés=["ne répond plus", "10 minutes"]

# 2. Classification
category = await classifier.classify("application web ne répond plus")
# → category=APP, subcategory=WEB_SERVER

# 3. Maestro dispatche investigations
maestro_plan = {
    "priority": "CRITICAL",
    "agents_to_call": [
        {"agent": "monitoring", "action": "check_server_status"},
        {"agent": "monitoring", "action": "check_logs"},
        {"agent": "browser", "action": "test_endpoint"},
    ]
}

# 4. Monitoring détecte
monitor_result = await monitoring.check_server_status()
# → nginx_status=DOWN, error="Connection refused"

# 5. Browser confirme
browser_result = await browser.browse("https://app.example.com")
# → status=502, error="Bad Gateway"

# 6. Maestro décide résolution
maestro_decision = {
    "diagnosis": "Nginx service stopped",
    "solution": "restart_nginx",
    "confidence": 0.95
}

# 7. DesktopCommander applique
cmd_result = await desktop_commander.execute("systemctl restart nginx")
# → success=True, output="nginx restarted successfully"

# 8. Backup + Verification
await backup.create_backup("pre_restart")
verify = await browser.browse("https://app.example.com")
# → status=200, success=True

# 9. Resolver marque résolu
await resolver.resolve_ticket(
    ticket_id="TICKET-123",
    resolution="Nginx service restarted automatically",
    actions_taken=["system_check", "service_restart", "verification"],
    time_to_resolve="2m 34s"
)

# 10. Monitoring continue surveillance
await monitoring.set_alert("nginx_health_check", interval="1m")
```

**Résultat**: Ticket résolu en <3 minutes, client satisfait, incident prévenu à l'avenir

---

## 📝 COMMITS & PULL REQUESTS

### Format de Commit
```bash
# Features
feat(maestro): implement LLM-based decision engine
feat(predictive): add ML failure prediction agent

# Fixes
fix(browser): handle timeout errors gracefully
fix(registry): improve agent lookup flexibility

# Docs
docs(readme): update architecture diagrams
docs(agents): add SentimentAnalyzer usage guide

# Tests
test(classifier): add edge cases for categories
test(e2e): add full ticket resolution scenario

# Refactor
refactor(agents): unify error handling across agents
refactor(api): simplify MCP route declarations
```

### Checklist PR
- [ ] Tests passent (`pytest`)
- [ ] Linting OK (`ruff + black`)
- [ ] Documentation mise à jour
- [ ] CHANGELOG.md enrichi
- [ ] Pas de secrets dans le code
- [ ] Agents testés individuellement
- [ ] Integration tests si nouveaux agents

---

## 🎓 PHILOSOPHIE DU PROJET

**Principes Fondamentaux**
1. **Simplicité > Complexité** - Si ça peut être plus simple, simplifions
2. **Autonomie des Agents** - Chaque agent doit pouvoir travailler seul
3. **Orchestration Intelligente** - Maestro coordonne mais n'impose pas
4. **Observabilité Totale** - Tout doit être loggé et mesurable
5. **Production-Ready** - Chaque feature doit être déployable immédiatement

**Ce Projet Prouve**
- Qu'on peut piloter l'IA pour résoudre de vrais problèmes
- Qu'une architecture multi-agents est viable en production
- Qu'un développeur déterminé peut créer des systèmes complexes
- Que l'automatisation intelligente est l'avenir du support technique

---

**🌀 TwisterLab - Parce que l'IA doit travailler pour nous, pas l'inverse.**
