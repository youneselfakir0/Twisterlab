import pytest

def test_health(client):
    """Verify the platform is healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["tools"] > 0
    print(f"\nPlatform Healthy. Tools detected: {data['tools']}")

def test_metrics_exposed(client):
    """Verify Prometheus metrics are exposed."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "process_cpu_seconds_total" in response.text
    
def test_tool_list_authenticated(client, admin_headers):
    """Verify tool list is accessible to admin."""
    response = client.get("/tools", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    
    tool_names = [t["name"] for t in data["tools"]]
    
    # Core Agents
    assert "monitoring_health_check" in tool_names
    assert "maestro_chat" in tool_names
    
    # Real Agents
    assert "sentiment-analyzer_analyze_sentiment" in tool_names
    assert "real-classifier_classify_ticket" in tool_names
    assert "real-resolver_resolve_ticket" in tool_names
    assert "real-backup_create_backup" in tool_names
    assert "code-review_analyze_code" in tool_names
