# 🌀 TwisterLab - Architecture MCP

## 📊 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TwisterLab v3.11                                    │
│                    Plateforme Multi-Agents MCP                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────┐         ┌───────────────────────┐               │
│  │   twisterlab-api      │         │    mcp-unified        │               │
│  │   Port: 30000         │         │    Port: 30080        │               │
│  │                       │         │                       │               │
│  │  ┌─────────────────┐  │         │  ┌─────────────────┐  │               │
│  │  │  REST API       │  │         │  │  MCP Protocol   │  │               │
│  │  │  FastAPI        │  │         │  │  JSON-RPC 2.0   │  │               │
│  │  │  Swagger /docs  │  │         │  │  29 Tools       │  │               │
│  │  │  Prometheus     │  │         │  │  SSE Support    │  │               │
│  │  └─────────────────┘  │         │  └─────────────────┘  │               │
│  └───────────────────────┘         └───────────────────────┘               │
│           │                                   │                             │
│           └───────────────┬───────────────────┘                             │
│                           │                                                 │
│  ┌────────────────────────┴────────────────────────┐                       │
│  │              Agents Layer (9 agents)            │                       │
│  ├─────────────────────────────────────────────────┤                       │
│  │ • SentimentAnalyzer  • RealClassifier           │                       │
│  │ • RealResolver       • RealBackup               │                       │
│  │ • RealMonitoring     • DesktopCommander         │                       │
│  │ • RealBrowser        • Maestro (Orchestrator)   │                       │
│  │ • RealSync                                      │                       │
│  └─────────────────────────────────────────────────┘                       │
│                           │                                                 │
│  ┌────────────────────────┴────────────────────────┐                       │
│  │              Data Layer                         │                       │
│  ├─────────────────────────────────────────────────┤                       │
│  │  PostgreSQL (5432)  │  Redis (6379)             │                       │
│  │  • Tickets          │  • Sessions               │                       │
│  │  • History          │  • Cache                  │                       │
│  └─────────────────────────────────────────────────┘                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔌 Points d'Accès

| Service | Port | URL | Protocole |
|---------|------|-----|-----------|
| **API REST** | 30000 | http://192.168.0.30:30000 | REST/HTTP |
| **MCP Server** | 30080 | http://192.168.0.30:30080/mcp | JSON-RPC 2.0 |
| **Prometheus** | 30090 | http://192.168.0.30:30090 | HTTP |
| **Grafana** | 30091 | http://192.168.0.30:30091 | HTTP |
| **Swagger Docs** | 30000 | http://192.168.0.30:30000/docs | HTTP |

## 🛠️ Les 29 Outils MCP

### Monitoring (7 outils)
| Outil | Description |
|-------|-------------|
| `monitoring_health_check` | Vérifie la santé des services |
| `monitoring_get_system_metrics` | Métriques système (CPU, RAM, Disk) |
| `monitoring_list_containers` | Liste les conteneurs Docker |
| `monitoring_get_container_logs` | Logs d'un conteneur |
| `monitoring_get_cache_stats` | Statistiques Redis |
| `monitoring_get_llm_status` | Status du serveur LLM |
| `monitoring_list_models` | Liste les modèles disponibles |

### Maestro - Orchestrateur (5 outils)
| Outil | Description |
|-------|-------------|
| `maestro_chat` | Chat avec le LLM |
| `maestro_generate` | Génération de texte |
| `maestro_orchestrate` | Orchestration multi-agents |
| `maestro_list_agents` | Liste des agents disponibles |
| `maestro_analyze` | Analyse de données |

### Database (4 outils)
| Outil | Description |
|-------|-------------|
| `database_execute_query` | Exécute une requête SQL |
| `database_list_tables` | Liste les tables |
| `database_describe_table` | Schéma d'une table |
| `database_db_health` | Santé de la base |

### Cache Redis (5 outils)
| Outil | Description |
|-------|-------------|
| `cache_cache_get` | Récupère une valeur |
| `cache_cache_set` | Stocke une valeur |
| `cache_cache_delete` | Supprime une clé |
| `cache_cache_keys` | Liste les clés |
| `cache_cache_stats` | Statistiques cache |

### Agents Autonomes (5 outils)
| Outil | Description |
|-------|-------------|
| `sentiment-analyzer_analyze_sentiment` | Analyse de sentiment |
| `real-classifier_classify_ticket` | Classification de tickets |
| `real-resolver_resolve_ticket` | Résolution de tickets |
| `real-backup_create_backup` | Création de sauvegardes |
| `real-desktop-commander_execute_command` | Exécution de commandes |

### Code & Browser (3 outils)
| Outil | Description |
|-------|-------------|
| `code-review_analyze_code` | Analyse de code |
| `code-review_security_scan` | Scan de sécurité |
| `browser_browse` | Navigation web |

## 📡 Utilisation du Protocole MCP

### Lister les outils disponibles
```bash
curl -X POST http://192.168.0.30:30080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Appeler un outil
```bash
# Analyse de sentiment
curl -X POST http://192.168.0.30:30080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"sentiment-analyzer_analyze_sentiment",
      "arguments":{"text":"This is great!"}
    }
  }'

# Classification de ticket
curl -X POST http://192.168.0.30:30080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"real-classifier_classify_ticket",
      "arguments":{"ticket_text":"Server is down"}
    }
  }'
```

### Réponse type
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "isError": false,
    "content": [
      {
        "type": "text",
        "text": "{\"sentiment\": \"positive\", \"confidence\": 0.8}"
      }
    ]
  }
}
```

## 📊 Métriques Prometheus

Les métriques sont exposées sur `/metrics` (port 30000) :

```prometheus
# Appels d'agents
agent_calls_total{agent_name="sentiment-analyzer",capability="analyze_sentiment"} 18
agent_execution_total{agent_name="sentiment-analyzer",status="success"} 18

# Latence
agent_latency_seconds_bucket{agent_name="sentiment-analyzer",le="0.01"} 18
agent_execution_duration_seconds_sum{agent_name="sentiment-analyzer"} 0.0005

# Orchestration Maestro
maestro_decisions_total{decision_type="dispatch"} 5
maestro_active_workflows 0
```

## 🏗️ Infrastructure Kubernetes

```yaml
Namespace: twisterlab
├── Deployments
│   ├── twisterlab-api (2 replicas, HPA 2-10)
│   ├── mcp-unified (1 replica, HPA 1-5)
│   ├── grafana (1 replica)
│   ├── redis (1 replica)
│   ├── postgres-exporter (1 replica)
│   └── redis-exporter (1 replica)
├── StatefulSets
│   └── postgres (1 replica)
└── Services
    ├── twisterlab-api (NodePort 30000)
    ├── mcp-unified (NodePort 30080)
    ├── grafana (NodePort 30300)
    ├── postgres (ClusterIP)
    └── redis (ClusterIP)

Namespace: monitoring
├── Deployments
│   ├── prometheus (1 replica)
│   └── grafana (1 replica)
└── Services
    ├── prometheus (NodePort 30090)
    └── grafana (NodePort 30091)
```

## 🎯 Flow de Traitement d'un Ticket

```
[Ticket Reçu] "Application ne répond plus depuis 2h"
       │
       ▼
┌──────────────────┐
│ SentimentAnalyzer│ → urgency: HIGH, sentiment: negative
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ RealClassifier   │ → category: APP/SERVER, priority: urgent
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Maestro          │ → Plan: [monitoring, browser, resolver]
│ (Orchestrateur)  │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Monitor │ │Browser │ → status: 502, nginx down
└───┬────┘ └───┬────┘
    │          │
    └────┬─────┘
         ▼
┌──────────────────┐
│ DesktopCommander │ → restart nginx
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ RealResolver     │ → ticket RESOLVED in 2m34s
└──────────────────┘
```

## 📈 Dashboards Grafana

- **Agent Dashboard** : Appels, latences, erreurs par agent
- **Infrastructure Dashboard** : CPU, RAM, pods, network
- **MCP Dashboard** : Outils appelés, temps de réponse

## 🔐 Sécurité

- PostgreSQL : Credentials via Secrets K8s
- Redis : Password protégé
- API : Rate limiting (20 req/min par IP)
- MCP : Validation JSON-RPC

## 📦 Versions

| Composant | Version |
|-----------|---------|
| TwisterLab API | v3.11 |
| MCP Unified | v3-fix |
| PostgreSQL | 16-alpine |
| Redis | 7-alpine |
| Python | 3.11 |
| K3s | Latest |

---

*Documentation générée le 2026-01-11*
*TwisterLab - L'IA qui travaille pour nous, pas l'inverse. 🌀*
