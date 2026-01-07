# 🤖 TwisterLab Agents Reference

> Quick reference for all 9 production agents

## Agent Registry

| # | Agent | Name | Description |
|---|-------|------|-------------|
| 1 | 🧠 Maestro | `maestro` | Orchestrates multi-agent workflows |
| 2 | 😊 Sentiment | `sentiment-analyzer` | Analyzes text sentiment and urgency |
| 3 | 🏷️ Classifier | `classifier` | Categorizes support tickets |
| 4 | 💻 Commander | `real-desktop-commander` | Executes system commands |
| 5 | ✅ Resolver | `resolver` | Marks tickets as resolved |
| 6 | 📊 Monitoring | `monitoring` | Collects system metrics |
| 7 | 💾 Backup | `backup` | Creates data backups |
| 8 | 🔄 Sync | `sync` | Synchronizes data between systems |
| 9 | 🌐 Browser | `browser` | Web automation and screenshots |

## Quick Reference

### Maestro (Orchestrator)

```python
# Analyze task
result = await maestro.execute("analyze_task", task="Server is down")
# Returns: {category, priority, suggested_agents}

# Full orchestration
result = await maestro.execute("orchestrate", task="DB slow", dry_run=False)
# Returns: {plan, execution_results, synthesis}
```

### Sentiment Analyzer

```python
result = await sentiment.execute("analyze_sentiment", 
    text="This is terrible!", 
    detailed=True
)
# Returns: {sentiment: "negative", confidence: 0.85, keywords: [...]}
```

### Classifier

```python
result = await classifier.execute("classify_ticket", 
    description="Database connection timeout"
)
# Returns: {category: "DATABASE", priority: "high"}
```

### Desktop Commander

```python
result = await commander.execute("execute_command",
    device_id="server-01",
    command="systemctl status nginx"
)
# Returns: {stdout, stderr, exit_code}
```

### Resolver

```python
result = await resolver.execute("resolve_ticket",
    ticket_id="TKT-2026-001",
    resolution_note="Fixed by restarting service"
)
# Returns: {status: "RESOLVED", resolved_at: "..."}
```

### Monitoring

```python
result = await monitoring.execute("get_system_metrics")
# Returns: {cpu: 45.2, memory: 62.1, disk: 78.5}

result = await monitoring.execute("check_service_health", 
    service_name="postgres"
)
# Returns: {healthy: true, response_time_ms: 12}
```

### Backup

```python
result = await backup.execute("create_backup",
    target="/data/postgres",
    backup_type="full"
)
# Returns: {backup_id: "...", path: "/backups/...", size_mb: 150}
```

### Sync

```python
result = await sync.execute("sync_data",
    source="server-a:/data",
    destination="server-b:/data"
)
# Returns: {synced_files: 42, total_size_mb: 256}
```

### Browser

```python
result = await browser.execute("browse", url="https://example.com")
# Returns: {status_code: 200, content: "...", title: "Example"}

result = await browser.execute("screenshot", url="https://example.com")
# Returns: {path: "/screenshots/...", format: "png"}
```

## API Endpoints

All agents are accessible via MCP endpoints:

```
POST /api/v1/mcp/analyze_sentiment
POST /api/v1/mcp/classify_ticket
POST /api/v1/mcp/resolve_ticket
POST /api/v1/mcp/create_backup
POST /api/v1/mcp/execute
GET  /api/v1/mcp/status
GET  /api/v1/agents
```

## Common Patterns

### Get Agent from Registry

```python
from twisterlab.agents.registry import agent_registry

# Get by name (flexible matching)
agent = agent_registry.get_agent("maestro")
agent = agent_registry.get_agent("sentiment-analyzer")
agent = agent_registry.get_agent("RealClassifierAgent")  # Also works

# List all agents
all_agents = agent_registry.list_agents()
```

### Execute with Error Handling

```python
async def safe_execute(agent_name: str, capability: str, **params):
    try:
        agent = agent_registry.get_agent(agent_name)
        result = await agent.execute(capability, **params)
        if result.success:
            return result.data
        else:
            logger.error(f"Agent error: {result.error}")
            return None
    except Exception as e:
        logger.exception(f"Execution failed: {e}")
        return None
```

### Chain Multiple Agents

```python
async def incident_workflow(ticket: str):
    # 1. Analyze sentiment
    sentiment = await agent_registry.get_agent("sentiment-analyzer").execute(
        "analyze_sentiment", text=ticket
    )
    
    # 2. Classify
    category = await agent_registry.get_agent("classifier").execute(
        "classify_ticket", description=ticket
    )
    
    # 3. Execute fix based on category
    if category.data["category"] == "DATABASE":
        await agent_registry.get_agent("real-desktop-commander").execute(
            "execute_command", 
            device_id="db-01", 
            command="pg_ctl restart"
        )
    
    # 4. Resolve
    await agent_registry.get_agent("resolver").execute(
        "resolve_ticket",
        ticket_id="TKT-AUTO",
        resolution_note="Auto-resolved"
    )
```

---

*TwisterLab v3.4.0 - January 2026*
