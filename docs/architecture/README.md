# 🌀 TwisterLab Architecture

> **Version**: 3.4.0 | **Date**: January 2026 | **Status**: Production Ready

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Agent Architecture](#agent-architecture)
4. [Orchestration Flow](#orchestration-flow)
5. [Data Flow](#data-flow)
6. [Deployment Architecture](#deployment-architecture)

---

## Overview

TwisterLab is an **autonomous multi-agent platform** for automated technical support. The system receives support tickets, analyzes them using AI, dispatches specialized agents, and resolves issues without human intervention.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Sentiment Analysis** | Detects urgency and customer emotion |
| **Ticket Classification** | Categorizes issues (database, network, security, etc.) |
| **Command Execution** | Runs system commands on target devices |
| **Web Automation** | Browser-based testing and verification |
| **Backup Management** | Creates safety backups before changes |
| **Resolution Tracking** | Marks tickets resolved with audit trail |

---

## System Architecture

### High-Level Overview

```mermaid
graph TB
    subgraph "External"
        TICKET[📝 Support Ticket]
        USER[👤 User/Customer]
    end
    
    subgraph "TwisterLab Platform"
        API[🌐 FastAPI Server<br/>Port 8000]
        
        subgraph "Agent Layer"
            MAESTRO[🧠 Maestro<br/>Orchestrator]
            SENT[😊 Sentiment<br/>Analyzer]
            CLASS[🏷️ Classifier]
            CMD[💻 Desktop<br/>Commander]
            MON[📊 Monitoring]
            RES[✅ Resolver]
            BACKUP[💾 Backup]
            SYNC[🔄 Sync]
            BROWSER[🌐 Browser]
        end
        
        subgraph "Data Layer"
            REDIS[(Redis<br/>Cache)]
            PG[(PostgreSQL<br/>Database)]
        end
    end
    
    subgraph "Infrastructure"
        OLLAMA[🤖 Ollama LLM]
        PROM[📈 Prometheus]
        GRAF[📊 Grafana]
    end
    
    TICKET --> API
    USER --> TICKET
    API --> MAESTRO
    MAESTRO --> SENT
    MAESTRO --> CLASS
    MAESTRO --> CMD
    MAESTRO --> MON
    MAESTRO --> RES
    MAESTRO --> BACKUP
    MAESTRO --> SYNC
    MAESTRO --> BROWSER
    
    API --> REDIS
    API --> PG
    MAESTRO -.-> OLLAMA
    API --> PROM
    PROM --> GRAF
```

### Component Details

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Server** | FastAPI + Uvicorn | REST API, MCP endpoints |
| **Agent Registry** | Python Singleton | Agent discovery & dispatch |
| **Maestro** | Custom LLM Agent | Orchestration & decision making |
| **Redis** | Redis 7.x | Caching, session management |
| **PostgreSQL** | PostgreSQL 15 | Persistent data storage |
| **Ollama** | Ollama + Mistral/Llama | Local LLM inference |

---

## Agent Architecture

### Agent Hierarchy

```mermaid
classDiagram
    class CoreAgent {
        <<abstract>>
        +name: str
        +description: str
        +get_capabilities() List~AgentCapability~
        +execute(capability_name, **kwargs) AgentResponse
    }
    
    class RealMaestroAgent {
        +handle_orchestrate(task, context, dry_run)
        +handle_analyze_task(task)
        -_llm_analyze(task)
        -_rule_based_analyze(task)
        -_create_plan(task, analysis)
        -_execute_plan(plan)
        -_synthesize_results(results)
    }
    
    class SentimentAnalyzerAgent {
        +handle_analyze_sentiment(text, detailed)
    }
    
    class RealClassifierAgent {
        +handle_classify_ticket(description)
    }
    
    class RealDesktopCommanderAgent {
        +handle_execute_command(device_id, command)
    }
    
    class RealResolverAgent {
        +handle_resolve_ticket(ticket_id, resolution_note)
    }
    
    class RealMonitoringAgent {
        +handle_get_system_metrics()
        +handle_check_service_health(service_name)
    }
    
    class RealBackupAgent {
        +handle_create_backup(target, backup_type)
    }
    
    class RealSyncAgent {
        +handle_sync_data(source, destination)
    }
    
    class BrowserAgent {
        +handle_browse(url)
        +handle_screenshot(url)
    }
    
    CoreAgent <|-- RealMaestroAgent
    CoreAgent <|-- SentimentAnalyzerAgent
    CoreAgent <|-- RealClassifierAgent
    CoreAgent <|-- RealDesktopCommanderAgent
    CoreAgent <|-- RealResolverAgent
    CoreAgent <|-- RealMonitoringAgent
    CoreAgent <|-- RealBackupAgent
    CoreAgent <|-- RealSyncAgent
    CoreAgent <|-- BrowserAgent
```

### Agent Capabilities

| Agent | Capability | Input | Output |
|-------|------------|-------|--------|
| **Maestro** | `orchestrate` | task, context, dry_run | execution_results |
| **Maestro** | `analyze_task` | task | category, priority, agents |
| **Sentiment** | `analyze_sentiment` | text, detailed | sentiment, confidence |
| **Classifier** | `classify_ticket` | description | category, priority |
| **Commander** | `execute_command` | device_id, command | stdout, stderr, exit_code |
| **Resolver** | `resolve_ticket` | ticket_id, note | status |
| **Monitoring** | `get_system_metrics` | - | cpu, memory, disk |
| **Backup** | `create_backup` | target, type | backup_id, path |
| **Browser** | `browse` | url | content, status |

---

## Orchestration Flow

### Ticket Resolution Sequence

```mermaid
sequenceDiagram
    participant T as 📝 Ticket
    participant API as 🌐 API
    participant M as 🧠 Maestro
    participant S as 😊 Sentiment
    participant C as 🏷️ Classifier
    participant CMD as 💻 Commander
    participant R as ✅ Resolver
    
    T->>API: POST /orchestrate
    API->>M: orchestrate(task)
    
    Note over M: Phase 1: Analysis
    M->>M: analyze_task()
    M-->>M: category: database<br/>priority: critical
    
    Note over M: Phase 2: Planning
    M->>M: create_plan()
    M-->>M: 4-step plan
    
    Note over M: Phase 3: Execution
    M->>S: analyze_sentiment(text)
    S-->>M: {sentiment: negative, urgency: high}
    
    M->>C: classify_ticket(text)
    C-->>M: {category: DATABASE, priority: high}
    
    M->>CMD: execute_command("pg_stat_activity")
    CMD-->>M: {output: "slow queries detected"}
    
    M->>R: resolve_ticket(id, note)
    R-->>M: {status: RESOLVED}
    
    Note over M: Phase 4: Synthesis
    M->>M: synthesize_results()
    M-->>API: {success: true, rate: 100%}
    API-->>T: Ticket Resolved ✅
```

### Decision Tree

```mermaid
flowchart TD
    START[📝 New Ticket] --> ANALYZE{🧠 Analyze Task}
    
    ANALYZE -->|database| DB[Database Issue]
    ANALYZE -->|network| NET[Network Issue]
    ANALYZE -->|security| SEC[Security Issue]
    ANALYZE -->|application| APP[Application Issue]
    
    DB --> SENT[😊 Check Sentiment]
    NET --> SENT
    SEC --> SENT
    APP --> SENT
    
    SENT -->|urgent| HIGH[🔴 High Priority]
    SENT -->|normal| MED[🟡 Medium Priority]
    SENT -->|calm| LOW[🟢 Low Priority]
    
    HIGH --> BACKUP[💾 Create Backup]
    MED --> CLASS[🏷️ Classify]
    LOW --> CLASS
    
    BACKUP --> CMD[💻 Execute Fix]
    CLASS --> CMD
    
    CMD --> VERIFY{Verify?}
    VERIFY -->|success| RESOLVE[✅ Resolve]
    VERIFY -->|failure| ESCALATE[👤 Escalate to Human]
    
    RESOLVE --> DONE[✅ Done]
    ESCALATE --> DONE
```

---

## Data Flow

### Request/Response Flow

```mermaid
flowchart LR
    subgraph "Client"
        REQ[HTTP Request]
    end
    
    subgraph "API Layer"
        ROUTE[FastAPI Route]
        MCP[MCP Handler]
    end
    
    subgraph "Agent Layer"
        REG[Agent Registry]
        AGENT[Target Agent]
    end
    
    subgraph "Response"
        RESP[AgentResponse]
        JSON[JSON Output]
    end
    
    REQ -->|POST /api/v1/mcp/*| ROUTE
    ROUTE -->|dispatch| MCP
    MCP -->|get_agent| REG
    REG -->|return| AGENT
    AGENT -->|execute| RESP
    RESP -->|serialize| JSON
    JSON -->|200 OK| REQ
```

### Data Models

```mermaid
erDiagram
    TICKET ||--o{ STEP : contains
    TICKET {
        string id PK
        string description
        string category
        string priority
        string status
        datetime created_at
        datetime resolved_at
    }
    
    STEP {
        int order PK
        string agent
        string capability
        json params
        string result
        boolean success
    }
    
    AGENT {
        string name PK
        string description
        json capabilities
        boolean active
    }
    
    EXECUTION {
        string task_id PK
        string ticket_id FK
        json plan
        json results
        float success_rate
        datetime executed_at
    }
    
    TICKET ||--|| EXECUTION : has
```

---

## Deployment Architecture

### Production Deployment

```mermaid
graph TB
    subgraph "Internet"
        CLIENT[🌐 Client]
    end
    
    subgraph "EdgeServer 192.168.0.30"
        subgraph "Docker Network"
            API[twisterlab-api<br/>:8001]
            MCP[twisterlab-mcp<br/>:8081]
            REDIS[Redis<br/>:6380]
            PG[PostgreSQL<br/>:5433]
            GRAF[Grafana<br/>:3001]
        end
        
        subgraph "Monitoring"
            PROM[Prometheus]
            NODE[Node Exporter]
            CADV[cAdvisor]
        end
        
        OLLAMA[Ollama<br/>:11434]
    end
    
    CLIENT --> API
    API --> REDIS
    API --> PG
    API --> MCP
    API -.-> OLLAMA
    PROM --> NODE
    PROM --> CADV
    PROM --> API
    GRAF --> PROM
```

### Container Configuration

| Container | Image | Port | Health |
|-----------|-------|------|--------|
| `twisterlab-api` | `twisterlab-api:v3.4.0` | 8001→8000 | ✅ |
| `twisterlab-redis` | `redis:7-alpine` | 6380→6379 | ✅ |
| `twisterlab-postgres` | `postgres:15` | 5433→5432 | ✅ |
| `twisterlab-grafana` | `grafana/grafana` | 3001→3000 | ✅ |
| `prometheus` | `prom/prometheus` | 9090 | ✅ |

### Environment Variables

```bash
# API Configuration
PYTHONPATH=/app/src
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/twisterlab
REDIS_URL=redis://redis:6379

# LLM Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=mistral

# Security
SECRET_KEY=<random-256-bit>
API_KEY_HEADER=X-API-Key
```

---

## Performance Metrics

### Benchmarks (Production)

| Metric | Value | Target |
|--------|-------|--------|
| **API Response Time** | <50ms | <100ms |
| **Orchestration Time** | ~2-5s | <10s |
| **Agent Dispatch** | <10ms | <50ms |
| **Success Rate** | 100% | >95% |
| **Memory Usage** | ~256MB | <512MB |

### Monitoring Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Basic health check |
| `/metrics` | Prometheus metrics |
| `/api/v1/mcp/status` | MCP server status |
| `/api/v1/agents` | List all agents |

---

## Next Steps

1. **Predictive Analytics** - ML model for incident prevention
2. **Multi-tenant** - Isolated environments per customer
3. **Workflow Builder** - Visual agent orchestration
4. **Knowledge Base** - Solution database for faster resolution

---

*Documentation generated: January 2026 | TwisterLab v3.4.0*
