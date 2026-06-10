# 🔌 TwisterLab MCP Configuration Guide

Configuration files for connecting IDE tools to the TwisterLab MCP Server.

## 📍 Server Information

| Property | Value |
|----------|-------|
| **K8s Node IP** | `192.168.0.30` (Edge Server / K3s) |
| **MCP Port** | `30080` |
| **FastAPI Endpoint** | `http://192.168.0.30:30080` |
| **MCP Tools API** | `http://192.168.0.30:30080/api/v1/mcp/tools` |
| **Health Check** | `http://192.168.0.30:30080/health` |
| **Readiness Check** | `http://192.168.0.30:30080/ready` |

> ⚠️ **Important**: Le serveur utilise HTTP (pas HTTPS). Pour Stdio/mcp-remote, ajouter `--allow-http`.


## 🛠️ Available Tools (20+ total)

### Agent Discovery
- `list_autonomous_agents` - Get all 20+ agents and capabilities
- `call_agent_tool` - Execute any agent capability

### Monitoring (2 tools)
- `monitoring_collect_metrics` - CPU, RAM, Disk, Network metrics
- `monitoring_system_health` - Full system health check

### Ticket Management (2 tools)
- `real-classifier_classify_ticket` - Classify tickets by category/priority
- `real-resolver_resolve_ticket` - Mark tickets as resolved

### Analysis (3 tools)
- `sentiment-analyzer_analyze_sentiment` - Text sentiment analysis
- `code-review_analyze_code` - Code quality analysis
- `code-review_security_scan` - Security vulnerability scan

### Operations (3 tools)
- `real-desktop-commander_execute_command` - Execute safe system commands
- `real-backup_create_backup` - Create backups
- `browser_browse` - Web browsing and content extraction

### Orchestration (2 tools)
- `maestro_orchestrate` - Multi-agent workflow coordination
- `maestro_analyze_task` - Task analysis and routing

---

## 🖥️ VS Code / GitHub Copilot

### Option 1: Workspace Settings (Recommended)
The `.vscode/settings.json` in this workspace is already configured.


### Option 2: User Settings

Add to your VS Code `settings.json`:

```json
{
    "mcp": {
        "servers": {
            "twisterlab": {
                "type": "sse",
                "url": "http://192.168.0.30:30080/api/v1/mcp/tools"
            }
        }
    },
    "github.copilot.chat.mcpServers": {
        "twisterlab": {
            "type": "sse",
            "url": "http://192.168.0.30:30080/api/v1/mcp/tools"
        }
    }
}
```

### Option 3: MCP Settings File

Create `~/.vscode/mcp.json`:

```json
{
    "servers": {
        "twisterlab": {
            "type": "sse",
            "url": "http://192.168.0.30:30080/api/v1/mcp/tools"
        }
    }
}
```

---

## 🔄 Continue IDE

### Installation
Copy `continue-config.yaml` to:
- **Linux/Mac**: `~/.continue/config.yaml`
- **Windows**: `%USERPROFILE%\.continue\config.yaml`

```powershell
# Windows
Copy-Item .\config\continue-config.yaml $env:USERPROFILE\.continue\config.yaml

# Linux/Mac
cp ./config/continue-config.yaml ~/.continue/config.yaml
```

### Manual Configuration
Add to your Continue config:

```yaml
experimental:
  modelContextProtocolServers:
    - name: "twisterlab"
      transport: "sse"
      url: "http://192.168.0.30:30080/api/v1/mcp/tools"
```

---

## 🤖 Claude Desktop

### Installation
Copy `claude_desktop_config.json` to:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```powershell
# Windows
Copy-Item .\config\claude_desktop_config.json $env:APPDATA\Claude\claude_desktop_config.json

# Mac
cp ./config/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Requirements
- Node.js 18+ (for npx)
- `mcp-remote` package (auto-installed via npx)

### Manual Configuration
Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "twisterlab": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://192.168.0.30:30080/api/v1/mcp/tools", "--allow-http"],
      "env": {
        "NODE_TLS_REJECT_UNAUTHORIZED": "0"
      }
    }
  }
}
```

---

## 🧪 Testing the Connection

### Quick Test (curl)

```bash
# Health check
curl http://192.168.0.30:30080/health

# List all agents
curl -X GET http://192.168.0.30:30080/api/v1/mcp/tools/list_autonomous_agents

# Call a specific agent tool
curl -X POST http://192.168.0.30:30080/api/v1/mcp/tools/call_agent_tool \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "classifier",
    "tool_name": "classify_ticket",
    "input": {"ticket_text": "Database is down"}
  }'
```

### Python Test

```python
import requests

# List agents
response = requests.get("http://192.168.0.30:30080/api/v1/mcp/tools/list_autonomous_agents")
print("Available agents:", response.json())

# Call a tool
response = requests.post(
    "http://192.168.0.30:30080/api/v1/mcp/tools/call_agent_tool",
    json={
        "agent_name": "classifier",
        "tool_name": "classify_ticket",
        "input": {"ticket_text": "The server is down!"}
    }
)
print("Classification result:", response.json())
```

### Load Test

```bash
ab -n 100 -c 10 http://192.168.0.30:30080/health
```

---

## 🔧 Troubleshooting

### Connection Refused

1. Check if MCP server is running:

```bash
kubectl get pods -n twisterlab -l app=twisterlab-api
```

2. Check service port:

```bash
kubectl get svc twisterlab-api -n twisterlab
```

### Endpoint Not Found

Verify the correct endpoint path is used:
- ✅ Correct: `http://192.168.0.30:30080/api/v1/mcp/tools/list_autonomous_agents`
- ❌ Wrong: `http://192.168.0.30:30080/mcp/list_autonomous_agents`

### Timeout Errors

Some agents (especially Maestro orchestration) can take 30-60 seconds. This is normal.

---

## 📁 Configuration Files

| File | Purpose |
| --- | --- |
| `config/vscode-mcp-config.json` | VS Code MCP settings template |
| `config/continue-config.yaml` | Continue IDE configuration |
| `config/claude_desktop_config.json` | Claude Desktop configuration |
| `.vscode/settings.json` | Workspace settings (active) |

---

🌀 **TwisterLab** - AI-powered support automation
