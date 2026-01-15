# 🔌 TwisterLab MCP Configuration Guide

Configuration files for connecting IDE tools to the TwisterLab MCP Server.

## 📍 Server Information

| Property | Value |
|----------|-------|
| **K8s Node IP** | `192.168.0.30` |
| **MCP Port** | `30080` |
| **JSON-RPC Endpoint** | `http://192.168.0.30:30080/mcp` |
| **Health Check** | `http://192.168.0.30:30080/health` |
| **Tools List** | `http://192.168.0.30:30080/tools` |

> ⚠️ **Important**: Le serveur utilise HTTP (pas HTTPS). Il faut ajouter `--allow-http` à mcp-remote.

## 🛠️ Available Tools (29 total)

### Monitoring (7 tools)
- `monitoring_health_check` - Check health of all services
- `monitoring_get_system_metrics` - Get CPU, memory, disk metrics
- `monitoring_list_containers` - List Docker containers
- `monitoring_get_container_logs` - Get container logs
- `monitoring_get_cache_stats` - Redis cache statistics
- `monitoring_get_llm_status` - Check LLM server status
- `monitoring_list_models` - List available LLM models

### Maestro/LLM (5 tools)
- `maestro_chat` - Send message to LLM
- `maestro_generate` - Generate text completion
- `maestro_orchestrate` - Orchestrate agent tasks
- `maestro_list_agents` - List all agents
- `maestro_analyze` - Analyze data/code with LLM

### Database (4 tools)
- `database_execute_query` - Execute SQL queries
- `database_list_tables` - List database tables
- `database_describe_table` - Get table schema
- `database_db_health` - Check database health

### Cache (5 tools)
- `cache_cache_get` - Get cached value
- `cache_cache_set` - Set cached value
- `cache_cache_delete` - Delete cached key
- `cache_cache_keys` - List cache keys
- `cache_cache_stats` - Cache statistics

### Agents (8 tools)
- `sentiment-analyzer_analyze_sentiment` - Analyze text sentiment
- `real-classifier_classify_ticket` - Classify support tickets
- `real-resolver_resolve_ticket` - Mark ticket resolved
- `real-backup_create_backup` - Create data backup
- `real-desktop-commander_execute_command` - Execute system commands
- `browser_browse` - Browse web pages
- `code-review_analyze_code` - Review code quality
- `code-review_security_scan` - Security scan code

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
                "url": "http://192.168.0.20:30080/sse"
            }
        }
    },
    "github.copilot.chat.mcpServers": {
        "twisterlab": {
            "type": "sse",
            "url": "http://192.168.0.20:30080/sse"
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
            "url": "http://192.168.0.20:30080/sse"
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
      url: "http://192.168.0.20:30080/sse"
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
      "args": ["-y", "mcp-remote", "http://192.168.0.20:30080/sse"]
    }
  }
}
```

---

## 🧪 Testing the Connection

### Quick Test (curl)
```bash
# Health check
curl http://192.168.0.20:30080/health

# List tools
curl -X POST http://192.168.0.20:30080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Python Test
```python
import requests

# Call a tool
response = requests.post(
    "http://192.168.0.20:30080/mcp",
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {
            "name": "monitoring_health_check",
            "arguments": {}
        }
    }
)
print(response.json())
```

### Load Test
```bash
python tests/load_test_mcp.py --quick
```

---

## 🔧 Troubleshooting

### Connection Refused
1. Check if MCP server is running:
   ```bash
   kubectl get pods -n twisterlab -l app=mcp-unified
   ```
2. Check service port:
   ```bash
   kubectl get svc mcp-unified -n twisterlab
   ```

### SSE Not Working
Try the stdio transport with npx:
```json
{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "mcp-remote", "http://192.168.0.20:30080/sse"]
}
```

### Timeout Errors
LLM-based tools (maestro_*) can take 30-60 seconds. This is normal.

---

## 📁 Configuration Files

| File | Purpose |
|------|---------|
| `config/vscode-mcp-config.json` | VS Code MCP settings template |
| `config/continue-config.yaml` | Continue IDE configuration |
| `config/claude_desktop_config.json` | Claude Desktop configuration |
| `.vscode/settings.json` | Workspace settings (active) |

---

🌀 **TwisterLab** - AI-powered support automation
