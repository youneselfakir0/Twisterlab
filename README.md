<div align="center"># TwisterLab Project



# 🌀 TwisterLab[![Codecov](https://codecov.io/gh/OWNER/REPO/branch/main/graph/badge.svg?token=REPLACE_TOKEN)](https://codecov.io/gh/OWNER/REPO)



### **Autonomous AI Agent Orchestration Platform**TwisterLab is a cloud-native, multi-agent AI infrastructure designed to facilitate complex tasks through autonomous agents. Built on a robust architecture using Python and FastAPI, TwisterLab leverages the Model Context Protocol (MCP) and a custom communication language, TwisterLang, to ensure efficient inter-agent communication and scalability.



[![CI Pipeline](https://github.com/youneselfakir0/twisterlab/actions/workflows/ci.yml/badge.svg)](https://github.com/youneselfakir0/twisterlab/actions/workflows/ci.yml)## Key Features

[![CD Pipeline](https://github.com/youneselfakir0/twisterlab/actions/workflows/cd.yml/badge.svg)](https://github.com/youneselfakir0/twisterlab/actions/workflows/cd.yml)

[![Security](https://github.com/youneselfakir0/twisterlab/actions/workflows/security.yml/badge.svg)](https://github.com/youneselfakir0/twisterlab/actions/workflows/security.yml)- **Autonomous Agents**: A suite of agents that collaborate to perform tasks such as monitoring, backups, and incident resolution.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)- **Cloud-Native Architecture**: Fully designed for deployment on Kubernetes, with a focus on CI/CD practices and automation.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)- **Structured Communication**: Utilizes TwisterLang for standardized, compressed, and observable communications between agents.

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)- **Flexible Deployment**: Supports real, hybrid, and mock modes for development and testing, ensuring versatility in various environments.

[![K8s](https://img.shields.io/badge/kubernetes-ready-326ce5.svg)](https://kubernetes.io/)

## Technology Stack

<br/>

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy v2

**Orchestrate intelligent AI agents that work autonomously, collaborate seamlessly, and scale infinitely.**- **Database**: PostgreSQL, Redis

- **Orchestration**: Kubernetes (k3s), Docker

[🚀 Quick Start](#-quick-start) •- **Monitoring**: Prometheus, Grafana

[📚 Documentation](#-documentation) •

[🤝 Contributing](#-contributing) •## Project Structure

[💬 Community](#-community)

- **src/twisterlab/api**: Contains the FastAPI application and its routes.

<br/>- **src/twisterlab/agents**: Houses the autonomous agents and their logic.

- **src/twisterlab/twisterlang**: Implements the TwisterLang protocol and its utilities.

<img src="docs/assets/architecture.png" alt="TwisterLab Architecture" width="800"/>- **k8s/**: Contains Kubernetes manifests for deployment and monitoring.

- **docs/**: Documentation for the project and its components.

</div>- **tests/**: Unit tests for various components of the project.

- **scripts/**: Utility scripts for scaffolding and logging.

---

## Getting Started

## ✨ Features

To get started with TwisterLab, clone the repository and install the required dependencies:

<table>

<tr>```bash

<td width="50%">git clone <repository-url>

cd TwisterLab

### 🤖 Autonomous Agentspip install -r requirements.txt

- **Maestro** - Orchestration & task routing```

- **Classifier** - Intelligent intent classification  

- **Resolver** - Issue resolution & debuggingNote: The SQL storage backend uses an async engine (SQLAlchemy Async); when running locally or in CI, set DATABASE_URL to use `sqlite+aiosqlite:///tests.sqlite3` or another async database driver like `postgresql+asyncpg://` for full compatibility.

- **Monitoring** - Real-time system health

- **Backup** - Automated data protection### Development helpers

- **Sync** - Cross-system synchronization

- **Browser** - Web automation & scrapingSecurity scan (detect-secrets + gitleaks):

- **Desktop** - Local system integration
- **CodeReview** - Automated analysis & security scanning1) Activate venv: `& C:/TwisterLab/venv/Scripts/Activate.ps1`

2) Run the helper: `python scripts/scan_secrets.py`

</td>

<td width="50%">Web UI (Browser Agent remote control):

1) Start the API server: `python -m uvicorn src.twisterlab.api.main:app --reload --port 8000`

### 🔧 MCP Integration2) Open the UI in your browser: `http://localhost:8000/ui/index.html`

- **39 MCP Tools** for VS Code & Continue IDE

- Natural language code generation### Running Playwright e2e tests locally

- Real-time project analysis

- Intelligent refactoring suggestionsIf you'd like to run the Playwright end-to-end UI tests locally:

- Multi-file context awareness

- Custom tool development SDK1. Build and run the API container or start the API with uvicorn (recommended to match CI):



</td>```bash

</tr>docker build -t twisterlab-api:latest -f Dockerfile.api .

<tr>docker run -d --name twisterlab-api-e2e -p 8000:8000 twisterlab-api:latest

<td># or run locally:

#   PYTHONPATH=src python -m uvicorn twisterlab.api.main:app --reload --port 8000

### 🧠 AI Capabilities```

- **Ollama LLM** integration (local models)

- Multi-model support (Llama, Mistral, CodeLlama)1. Install test requirements and Playwright browsers (cross-platform):

- Retrieval-Augmented Generation (RAG)

- Vector embeddings for semantic searchOn Linux/macOS or WSL:

- Conversation memory & context

```bash

</td>pip install -r requirements.txt

<td>python -m playwright install --with-deps chromium

```

### 🏗️ Enterprise Ready

- **Kubernetes** native deploymentOn Windows PowerShell:

- **Prometheus** + **Grafana** monitoring

- **PostgreSQL** persistence```powershell

- **Redis** caching & pub/subpython -m pip install -r requirements.txt

- Multi-tenant architecturepython -m playwright install --with-deps chromium

- Horizontal auto-scaling (HPA)
- E2E Testing Pipeline (Pytest + Playwright)```



</td>1. Run the tests (the E2E tests are only enabled when E2E=1):

</tr>

</table>On Linux/macOS:



---```bash

E2E=1 pytest -q -m e2e

## 🏛️ Architecture```



```On Windows PowerShell:

┌─────────────────────────────────────────────────────────────────────────┐

│                           🌀 TwisterLab                                  │```powershell

├─────────────────────────────────────────────────────────────────────────┤$env:E2E = '1'

│                                                                          │pytest -q -m e2e

│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐   │```

│  │   VS Code    │    │  Continue    │    │       CLI / API          │   │

│  │  Extension   │    │     IDE      │    │    (REST / WebSocket)    │   │Artifacts (screenshots & traces) will be saved under the `artifacts/` directory when tests fail.

│  └──────┬───────┘    └──────┬───────┘    └────────────┬─────────────┘   │

│         │                   │                          │                 │

│         └───────────────────┴──────────────────────────┘                 │### Running the Application

│                              │                                           │

│                    ┌─────────▼─────────┐                                 │You can run the FastAPI application locally using:

│                    │    MCP Gateway    │  ◄── 39 MCP Tools               │

│                    │    (FastAPI)      │                                 │```bash

│                    └─────────┬─────────┘                                 │python -m uvicorn src.twisterlab.api.main:app --reload --port 8000

│                              │                                           │```

│         ┌────────────────────┼────────────────────┐                      │

│         │                    │                    │                      │### Deployment

│   ┌─────▼─────┐       ┌──────▼──────┐      ┌─────▼─────┐                │

│   │  Maestro  │       │  Classifier │      │  Resolver │                │TwisterLab can be deployed on Kubernetes using the provided manifests in the `k8s/deployments` directory. Ensure that your Kubernetes cluster is set up and configured before deploying.

│   │  Agent    │◄─────►│    Agent    │◄────►│   Agent   │                │

│   └─────┬─────┘       └─────────────┘      └───────────┘                │## Contributing

│         │                                                                │

│   ┌─────▼──────────────────────────────────────────────────────┐        │Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.

│   │                    Agent Pool                               │        │

│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │        │## License

│   │  │Monitoring│ │  Backup  │ │   Sync   │ │  Browser │       │        │

│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │        │This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
│   └────────────────────────────────────────────────────────────┘        │
│                              │                                           │
│         ┌────────────────────┼────────────────────┐                      │
│         │                    │                    │                      │
│   ┌─────▼─────┐       ┌──────▼──────┐      ┌─────▼─────┐                │
│   │ PostgreSQL│       │    Redis    │      │  Ollama   │                │
│   │    DB     │       │   Cache     │      │   LLM     │                │
│   └───────────┘       └─────────────┘      └───────────┘                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 24.0+ & Docker Compose
- **Python** 3.11+
- **Git**

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/youneselfakir0/twisterlab.git
cd twisterlab

# Start all services
docker compose up -d

# Verify
curl http://localhost:8000/health
```

### Option 2: Local Development

```bash
# Clone and setup
git clone https://github.com/youneselfakir0/twisterlab.git
cd twisterlab

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Start services
docker compose up -d postgres redis ollama

# Run the API
uvicorn src.twisterlab.api.main:app --reload
```

### Option 3: Kubernetes

```bash
# Apply manifests
kubectl apply -k deploy/k8s/base/

# Or with overlays
kubectl apply -k deploy/k8s/overlays/staging/
```

---

## 📦 Project Structure

```
twisterlab/
├── 📁 src/twisterlab/          # Source code
│   ├── 📁 agents/              # Autonomous agents
│   ├── 📁 api/                 # FastAPI application
│   ├── 📁 mcp/                 # MCP server & tools
│   ├── 📁 db/                  # Database & migrations
│   └── 📁 twisterlang/         # Domain-specific language
│
├── 📁 deploy/                  # Deployment configs
│   ├── 📁 docker/              # Dockerfiles
│   ├── 📁 k8s/                 # Kubernetes manifests
│   │   ├── 📁 base/            # Base resources
│   │   └── 📁 overlays/        # Environment configs
│   └── 📁 scripts/             # Automation scripts
│
├── 📁 monitoring/              # Observability stack
│   ├── 📁 grafana/             # Dashboards
│   └── 📁 prometheus/          # Metrics config
│
├── 📁 docs/                    # Documentation
│   ├── 📁 api/                 # API reference
│   ├── 📁 architecture/        # Design docs
│   └── 📁 guides/              # User guides
│
├── 📁 tests/                   # Test suite
├── 📄 docker-compose.yml       # Local dev stack
├── 📄 pyproject.toml           # Python project config
└── 📄 README.md               # This file
```

---

## 🔌 MCP Tools

TwisterLab provides **39 MCP tools** for seamless IDE integration:

| Category | Tools | Description |
|----------|-------|-------------|
| 🔍 **Analysis** | `analyze_code`, `find_issues`, `suggest_fixes` | Code intelligence |
| 🛠️ **Refactoring** | `refactor_function`, `extract_method`, `rename_symbol` | Automated refactoring |
| 📝 **Generation** | `generate_code`, `create_tests`, `write_docs` | AI-powered generation |
| 🔄 **Integration** | `sync_project`, `deploy_changes`, `rollback` | DevOps automation |
| 📊 **Monitoring** | `check_health`, `view_metrics`, `analyze_logs` | System observability |

### VS Code Integration

```json
// .vscode/settings.json
{
  "mcp.servers": {
    "twisterlab": {
      "command": "python",
      "args": ["-m", "twisterlab.mcp"]
    }
  }
}
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run E2E Tests (Requires Platform Running)
export MCP_API_URL="http://192.168.0.30:30001"
pytest tests/e2e/

# With coverage
pytest --cov=src/twisterlab --cov-report=html

# Specific test file
pytest tests/test_agents.py -v

# Integration tests
pytest tests/integration/ -v --slow
```

---

## 📊 Monitoring

TwisterLab includes a complete observability stack:

- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards
- **Loki** - Log aggregation
- **Jaeger** - Distributed tracing

Access dashboards:
```bash
# Grafana
http://localhost:3000  # admin:admin

# Prometheus
http://localhost:9090
```

---

## 🔐 Security

- 🔒 All endpoints require authentication
- 🛡️ Role-based access control (RBAC)
- 🚦 **Rate Limiting**: Custom Middleware (60 req/min/IP) to prevent abuse.
- 🌐 **Network Policies**: Kubernetes "Default Deny" + Whitelist Ingress.
- 📝 Audit logging enabled
- 🔑 Secrets management via K8s secrets
- 🔍 Automated security scanning in CI/CD pipeline

Report vulnerabilities: [security@twisterlab.io](mailto:security@twisterlab.io)

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
> 💡 All Pull Requests are automatically tested via our **GitHub Actions CI**. Please ensure tests pass before requesting review.

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/twisterlab.git

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
pytest

# Commit with conventional commits
git commit -m "feat: add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💬 Community

- 📧 Email: [contact@twisterlab.io](mailto:contact@twisterlab.io)
- 🐛 Issues: [GitHub Issues](https://github.com/youneselfakir0/twisterlab/issues)
- 💡 Discussions: [GitHub Discussions](https://github.com/youneselfakir0/twisterlab/discussions)

---

<div align="center">

**Built with ❤️ by [Younes El Fakir](https://github.com/youneselfakir0)**

⭐ Star this repo if you find it useful!

</div>
