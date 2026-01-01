<div align="center">

# 🌀 TwisterLab v3.3.0

[![CI Pipeline](https://github.com/youneselfakir0/twisterlab/actions/workflows/ci.yml/badge.svg)](https://github.com/youneselfakir0/twisterlab/actions/workflows/ci.yml)
[![CD Pipeline](https://github.com/youneselfakir0/twisterlab/actions/workflows/cd.yml/badge.svg)](https://github.com/youneselfakir0/twisterlab/actions/workflows/cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![K8s](https://img.shields.io/badge/kubernetes-ready-326ce5.svg)](k8s/)

### **Universal MCP Platform for Autonomous AI Agents**

TwisterLab acts as a bridge between LLMs (**Claude**, **Ollama**) and your infrastructure. It exposes specialized Agents (Browser, Monitoring, Code Review) via the standardized **Model Context Protocol (MCP)**.

[🚀 Quick Start](#-quick-start) • [📚 Documentation](docs/) • [🤝 Contributing](#-contributing)

</div>

---

## 🏗️ Architecture

TwisterLab is built as a **Hybrid AI Operating System**:

- **Core API**: FastAPI + Python 3.11 (Async)
- **Transport**: Native MCP (Stdio & SSE)
- **Agents**:
  - 🌍 **Browser Agent**: Headless Chromium (Playwright) for web automation.
  - 🧐 **Code Review Agent**: Native static analysis (AST/Security).
  - 📈 **Monitoring Agent**: Real-time system health & K8s metrics.
- **Infrastructure**:
  - **Kubernetes**: Scalable deployment (Deployment, Service, HPA).
  - **Docker**: Containerized runtime.
  - **Ollama**: Remote LLM inference (Llama, Mistral, Qwen).

---

## ✨ Key Features

1.  **🔌 Seamless Integration**: Connects natively to **Claude Desktop**, **Continue IDE**, and **LM Studio**.
2.  **🕸️ Real Web Browsing**: Not just a mock. TwisterLab drives a real browser to fetch pages, take screenshots, and extract content via MCP.
3.  **🛡️ Security First**: Rate limiting, Network Policies (K8s), and hardcoded secret scanning.
4.  **⚡ High Performance**: Redis caching and async Pydantic validation.

---

## 🚀 Quick Start

### 1. Requirements
- **Docker** & **Kubernetes** (k3d, minikube, or bare metal).
- **Python 3.11+** (for local dev).

### 2. Configure Claude Desktop ("Pro Mode")

To give Claude access to your Kubernetes cluster agents:

**File**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "TwisterLab": {
      "command": "kubectl",
      "args": [
        "exec",
        "-i",
        "-n",
        "twisterlab",
        "deployment/twisterlab-api",
        "--",
        "python",
        "-m",
        "twisterlab.agents.mcp.server"
      ]
    }
  }
}
```

### 3. Local Development (Optional)

If you don't use Kubernetes, you can run the server locally:

```bash
# Install dependencies including Playwright
pip install poetry
poetry install
poetry run playwright install chromium

# Run server with SSE support
export PYTHONPATH=src
python -m uvicorn twisterlab.api.main:app --port 8000 --reload
```

---

## 📦 Project Structure

```
twisterlab/
├── 📁 src/twisterlab/          # Application Core
│   ├── 📁 agents/              # Autonomous Agents (Real Implementations)
│   │   ├── 📁 real/            # Browser, CodeReview, Monitoring
│   │   └── 📁 mcp/             # MCP Server Logic (Stdio/SSE)
│   ├── 📁 api/                 # FastAPI Routes & Main entrypoint
│   └── 📁 db/                  # Database Models (SQLAlchemy)
│
├── 📁 deploy/                  # Deployment Configurations
│   ├── 📁 docker/              # Dockerfiles (API, Agents)
│   └── 📁 k8s/                 # Kubernetes Manifests
│
├── 📁 monitoring/              # Observability (Grafana/Prometheus)
├── 📁 tests/                   # Pytest & Performance Benchmarks
└── 📄 pyproject.toml           # Dependencies
```

---

## 🧪 Testing

```bash
# Run Unit Tests
pytest

# Run End-to-End Tests (requires environment)
export E2E=1
pytest -m e2e
```

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md).

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes.
4. Push to the branch.
5. Open a Pull Request.

---

<div align="center">
Built with ❤️ by Younes El Fakir for the AI Community.
</div>
