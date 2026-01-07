# 🌀 TwisterLab - GitHub Copilot Instructions

## 🎯 MISSION DU PROJET
**Automatisation complète du support technique via agents IA autonomes**

TwisterLab = Plateforme multi-agents qui :
- Reçoit tickets support → Analyse → Recherche solutions → Applique fixes → Prévient récidives
- Agents autonomes orchestrés par un "cerveau" IA (Maestro)
- Monitoring prédictif pour prévenir incidents AVANT qu'ils arrivent
- Cible : PME qui veulent support technique 24/7 intelligent

## 🧠 ARCHITECTURE - Comment Ça Marche

```
[TICKET] "Base de données lente"
    ↓
🧠 MAESTRO (Cerveau LLM) - Analyse + Dispatche
    ├─ 😊 SentimentAnalyzer → Urgence client
    ├─ 🏷️ Classifier → Catégorise problème
    ├─ 📊 Monitoring → Collecte métriques
    ├─ 🌐 Browser → Recherche solutions web
    ├─ 💻 DesktopCommander → Exécute commandes
    ├─ ✅ Resolver → Applique solution
    └─ 💾 Backup → Sécurise avant action
    ↓
[RÉSOLU] + Monitoring préventif
```

**9 Agents Actifs** (dans `src/twisterlab/agents/real/`)
1. RealMaestroAgent - Orchestrateur intelligent (À IMPLÉMENTER COMPLÈTEMENT)
2. SentimentAnalyzerAgent - Détecte urgence
3. RealClassifierAgent - Catégorise tickets
4. RealMonitoringAgent - Santé système
5. RealBrowserAgent - Recherche web (Playwright)
6. RealDesktopCommanderAgent - Exécution commandes
7. RealResolverAgent - Marque résolu
8. RealBackupAgent - Sécurise données
9. RealSyncAgent - Synchro systèmes

## 🔧 STACK TECHNIQUE

**Core**
- Python 3.11+ | FastAPI async | SQLAlchemy async
- PostgreSQL (asyncpg) | Redis cache
- Playwright (browser automation)

**Infrastructure**
- Docker (images 265MB optimisées)
- Kubernetes (k3s/minikube/cloud)
- Prometheus + Grafana monitoring

**IA/LLM**
- MCP (Model Context Protocol)
- Ollama (local) ou Claude (API)
- Agents capability-based

## ⚠️ PIÈGES CRITIQUES

### ❌ ERREUR FATALE #1 - Database
```python
# ❌ CRASH L'APP
from sqlalchemy import create_engine
DATABASE_URL = "postgresql://..."

# ✅ OBLIGATOIRE
from sqlalchemy.ext.asyncio import create_async_engine
DATABASE_URL = "postgresql+asyncpg://..."
```

### ❌ ERREUR FATALE #2 - Pydantic
```python
# ❌ Pydantic v1 (obsolète)
model.dict()

# ✅ Pydantic v2
model.model_dump()
```

### ✅ Patterns Corrects
```python
# Import session
from twisterlab.database.session import AsyncSessionLocal, get_db

# Tests avec markers
@pytest.mark.asyncio
@pytest.mark.unit
async def test_something(): ...

# Agent lookup flexible
registry.get_agent("classifier")           # ✅
registry.get_agent("real-classifier")      # ✅
registry.get_agent("RealClassifierAgent")  # ✅
```

## 📁 STRUCTURE CLÉS

```
src/twisterlab/
├── agents/
│   ├── real/              # 9 agents autonomes
│   ├── core/base.py       # Classes de base (TwisterAgent, CoreAgent)
│   ├── registry.py        # Singleton registry
│   └── mcp/               # Serveur MCP
├── api/
│   ├── main.py            # FastAPI app
│   └── routes_mcp_real.py # 39+ endpoints MCP
└── database/session.py    # Async sessions

tests/
├── unit/                  # Tests rapides isolés
├── integration/           # Tests multi-composants
└── e2e/                   # Tests Playwright

k8s/
├── base/                  # ConfigMaps, Secrets
├── deployments/           # Deployments par service
└── monitoring/            # Prometheus/Grafana

docs/                      # Docs complètes
deploy/docker/             # Dockerfiles
scripts/                   # DevOps tools
```

## 🚀 COMMANDES RAPIDES

```bash
# Dev local
uvicorn src.twisterlab.api.main:app --reload --port 8000

# Tests
pytest tests/unit -v                   # Unitaires
pytest tests/integration -v            # Intégration
$env:E2E='1'; pytest -m e2e -v        # E2E

# Linting (obligatoire!)
ruff check src tests
black src tests

# Docker
docker-compose up -d                   # Stack complète
docker-compose logs -f api

# K8s
kubectl apply -f k8s/base/ k8s/deployments/
kubectl get pods -n twisterlab
```

## 🎓 CRÉER UN NOUVEL AGENT

### 1. Scaffold
```bash
python scripts/new_agent_scaffold.py --name MyAgent
```

### 2. Implémenter (Template)
```python
# src/twisterlab/agents/real/my_agent.py
from twisterlab.agents.core.base import (
    TwisterAgent, AgentCapability, AgentResponse,
    CapabilityType, CapabilityParam, ParamType
)

class MyAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "my-agent"
    
    @property
    def description(self) -> str:
        return "Description claire de ce que fait l'agent"
    
    def get_capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="do_action",
                description="Action description",
                handler="handle_do_action",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("input", ParamType.STRING, "Description", required=True)
                ]
            )
        ]
    
    async def handle_do_action(self, input: str) -> AgentResponse:
        # Logique ici
        return AgentResponse(success=True, data={"result": input})
```

### 3. Enregistrer
```python
# src/twisterlab/agents/registry.py
from twisterlab.agents.real.my_agent import MyAgent

class AgentRegistry:
    def initialize_agents(self):
        my_agent = MyAgent()
        self._agents = {
            # ...autres...
            my_agent.name.lower(): my_agent,
        }
```

### 4. Endpoint MCP
```python
# src/twisterlab/api/routes_mcp_real.py
@router.post("/do_action")
async def do_action(request: ActionRequest):
    agent = agent_registry.get_agent("my-agent")
    result = await agent.handle_do_action(request.input)
    return MCPResponse(status="ok" if result.success else "error", data=result.data)
```

### 5. Tests
```python
# tests/unit/test_my_agent.py
@pytest.mark.asyncio
@pytest.mark.unit
async def test_my_agent_success():
    agent = MyAgent()
    result = await agent.handle_do_action("test")
    assert result.success is True
```

## 🎯 PRIORITÉS ACTUELLES

### 🔴 URGENT
1. **Implémenter RealMaestroAgent complet** - Le cerveau orchestrateur
2. **Démo end-to-end** - Scénario "Database lente" → Résolution auto
3. **Documentation visuelle** - Diagrammes architecture + vidéos

### 🟡 IMPORTANT
4. Agent prédictif ML (prévenir pannes)
5. Dashboard Grafana custom
6. Tests E2E automatisés

## 🛡️ SÉCURITÉ

```bash
# ❌ JAMAIS commit
.env
*.key
secrets.yaml (non-template)

# ✅ Variables critiques
DATABASE_URL=postgresql+asyncpg://...  # Async!
REDIS_URL=redis://...
SECRET_KEY=<random>
OLLAMA_BASE_URL=http://localhost:11434
PYTHONPATH=src
```

## 📊 MONITORING

```python
# Métriques Prometheus custom
from prometheus_client import Counter, Histogram

agent_calls = Counter('agent_calls_total', 'Total calls', ['agent_name'])
agent_duration = Histogram('agent_duration_seconds', 'Duration', ['agent_name'])

# Endpoints
/health      # Santé API
/metrics     # Prometheus
/docs        # Swagger
```

## 💡 GUIDELINES COPILOT

### Avant de Générer du Code
1. ✅ Aligné avec la vision (support technique automatisé) ?
2. ✅ Aide vraiment à résoudre des tickets ?
3. ✅ Complexité justifiée ?
4. ✅ Code existant réutilisable ?

### Patterns à Privilégier
```python
# Async partout
async def process(): ...

# Type hints stricts
def func(data: dict[str, Any]) -> AgentResponse: ...

# Error handling explicite
try:
    result = await agent.execute()
except Exception as e:
    logger.error(f"Failed: {e}")
    return AgentResponse(success=False, error=str(e))

# Logging informatif
logger.info(f"🚀 {self.name} starting: {task_id}")
```

### Format Commits
```bash
feat(maestro): implement LLM decision engine
fix(browser): handle timeout gracefully
docs(readme): add architecture diagrams
test(e2e): add ticket resolution scenario
refactor(agents): unify error handling
```

### Checklist PR
- [ ] Tests passent
- [ ] Linting OK (ruff + black)
- [ ] Docs mises à jour
- [ ] CHANGELOG enrichi
- [ ] Pas de secrets
- [ ] Tests agents individuels

## 🎬 EXEMPLE COMPLET

**Scénario**: "Application web ne répond plus"

```python
# 1. Sentiment → urgence=HIGH
sentiment = await sentiment_agent.analyze("ne répond plus depuis 10 minutes")

# 2. Classifier → category=APP/WEB_SERVER
category = await classifier.classify("application web ne répond plus")

# 3. Maestro dispatche
maestro_plan = {
    "agents": ["monitoring", "browser"],
    "actions": ["check_status", "test_endpoint"]
}

# 4. Monitoring détecte
status = await monitoring.check_server_status()
# → nginx_status=DOWN

# 5. Browser confirme
test = await browser.browse("https://app.example.com")
# → status=502

# 6. Maestro décide
decision = {"solution": "restart_nginx", "confidence": 0.95}

# 7. DesktopCommander exécute
result = await desktop_commander.execute("systemctl restart nginx")

# 8. Verification
verify = await browser.browse("https://app.example.com")
# → status=200 ✅

# 9. Resolver marque résolu
await resolver.resolve_ticket("TICKET-123", "Nginx restarted - 2m34s")

# 10. Monitoring continue
await monitoring.set_alert("nginx_health_check", interval="1m")
```

**Résultat**: Ticket résolu en <3min, client satisfait, prévention future activée

## 📖 DOCUMENTATION CLÉS

- **README.md** - Vue d'ensemble
- **QUICKSTART.md** - Démarrage rapide
- **docs/architecture/** - Diagrammes
- **docs/agents/** - Guide par agent
- **DEPLOYMENT.md** - Guide déploiement

## 🌟 PHILOSOPHIE

1. **Simplicité > Complexité**
2. **Autonomie des Agents** - Chaque agent indépendant
3. **Orchestration Intelligente** - Maestro coordonne
4. **Observabilité Totale** - Tout loggé/mesuré
5. **Production-Ready** - Déployable immédiatement

**Ce Projet Prouve**: Qu'on peut piloter l'IA pour résoudre de vrais problèmes en production.

---

🌀 **TwisterLab** - L'IA qui travaille pour nous, pas l'inverse.
