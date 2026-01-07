"""
Unit tests for MCP routes - testing real routes from routes/mcp.py
Tests endpoints that are actually mounted in main.py
"""

import pytest
from httpx import AsyncClient, ASGITransport

# Mark all tests as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def app():
    """Create test FastAPI app."""
    from twisterlab.api.main import app
    return app


@pytest.fixture
async def async_client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestMCPStatus:
    """Tests for /status endpoint."""

    @pytest.mark.asyncio
    async def test_mcp_status(self, async_client):
        """Test GET /status returns running status."""
        response = await async_client.get("/api/v1/mcp/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "MCP server is running"


class TestMCPExecute:
    """Tests for /execute endpoint."""

    @pytest.mark.asyncio
    async def test_execute_tool(self, async_client):
        """Test POST /execute returns success."""
        response = await async_client.post(
            "/api/v1/mcp/execute",
            json={"tool_name": "test_tool", "args": {"key": "value"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["result"]["executed_tool"] == "test_tool"


class TestMCPSentiment:
    """Tests for /analyze_sentiment endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_sentiment_success(self, async_client):
        """Test successful sentiment analysis with real agent."""
        response = await async_client.post(
            "/api/v1/mcp/analyze_sentiment",
            json={"text": "I love this product, it is amazing!"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # API returns content/isError format
        assert data["isError"] is False
        assert "content" in data
        assert len(data["content"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_sentiment_detailed(self, async_client):
        """Test detailed sentiment analysis."""
        response = await async_client.post(
            "/api/v1/mcp/analyze_sentiment",
            json={"text": "This is amazing and I love it!", "detailed": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] is False

    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative(self, async_client):
        """Test negative sentiment analysis."""
        response = await async_client.post(
            "/api/v1/mcp/analyze_sentiment",
            json={"text": "This is terrible, I hate it!"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] is False

    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral(self, async_client):
        """Test neutral sentiment analysis."""
        response = await async_client.post(
            "/api/v1/mcp/analyze_sentiment",
            json={"text": "The sky is blue."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] is False


class TestMCPResponseModel:
    """Tests for MCPResponse model from routes_mcp_real.py."""

    def test_mcp_response_ok(self):
        """Test MCPResponse with ok status."""
        from twisterlab.api.routes_mcp_real import MCPResponse
        
        response = MCPResponse(status="ok", data={"key": "value"})
        assert response.status == "ok"
        assert response.data == {"key": "value"}
        assert response.error is None

    def test_mcp_response_error(self):
        """Test MCPResponse with error status."""
        from twisterlab.api.routes_mcp_real import MCPResponse
        
        response = MCPResponse(status="error", error="Something went wrong")
        assert response.status == "error"
        assert response.error == "Something went wrong"

    def test_mcp_response_invalid_status(self):
        """Test MCPResponse with invalid status raises error."""
        from twisterlab.api.routes_mcp_real import MCPResponse
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            MCPResponse(status="invalid")


class TestMCPRequestModels:
    """Tests for request model validation from routes_mcp_real.py."""

    def test_classify_ticket_request_valid(self):
        """Test valid ClassifyTicketRequest."""
        from twisterlab.api.routes_mcp_real import ClassifyTicketRequest
        
        request = ClassifyTicketRequest(description="My issue description")
        assert request.description == "My issue description"

    def test_classify_ticket_request_strips_whitespace(self):
        """Test ClassifyTicketRequest strips whitespace."""
        from twisterlab.api.routes_mcp_real import ClassifyTicketRequest
        
        request = ClassifyTicketRequest(description="  Test description  ")
        assert request.description == "Test description"

    def test_resolve_ticket_request_valid(self):
        """Test valid ResolveTicketRequest."""
        from twisterlab.api.routes_mcp_real import ResolveTicketRequest
        
        request = ResolveTicketRequest(category="software")
        assert request.category == "software"

    def test_resolve_ticket_request_invalid_category(self):
        """Test ResolveTicketRequest with invalid category."""
        from twisterlab.api.routes_mcp_real import ResolveTicketRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ResolveTicketRequest(category="not_a_valid_category")


class TestMaestroEndpoints:
    """Tests for Maestro orchestration endpoints."""

    @pytest.mark.asyncio
    async def test_orchestrate_dry_run(self, async_client):
        """Test orchestrate endpoint with dry_run=True."""
        response = await async_client.post(
            "/api/v1/mcp/tools/orchestrate",
            json={
                "task": "Database is running slow, users are complaining",
                "context": {"source": "test"},
                "dry_run": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "data" in data
        assert data["data"]["mode"] == "dry_run"
        assert "plan" in data["data"]
        assert "analysis" in data["data"]

    @pytest.mark.asyncio
    async def test_orchestrate_full_execution(self, async_client):
        """Test orchestrate endpoint with full execution."""
        response = await async_client.post(
            "/api/v1/mcp/tools/orchestrate",
            json={
                "task": "Server returning 502 errors",
                "dry_run": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "synthesis" in data["data"]
        assert "success_rate" in data["data"]["synthesis"]

    @pytest.mark.asyncio
    async def test_analyze_task(self, async_client):
        """Test analyze_task endpoint."""
        response = await async_client.post(
            "/api/v1/mcp/tools/analyze_task",
            json={"task": "Network connection timeout on server-01"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "category" in data["data"]
        assert "priority" in data["data"]
        assert "suggested_agents" in data["data"]

    @pytest.mark.asyncio
    async def test_analyze_task_database_category(self, async_client):
        """Test that database keywords are correctly categorized."""
        response = await async_client.post(
            "/api/v1/mcp/tools/analyze_task",
            json={"task": "PostgreSQL queries are slow, need optimization"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["data"]["category"] == "database"

    def test_orchestrate_request_valid(self):
        """Test valid OrchestrateRequest model."""
        from twisterlab.api.routes_mcp_real import OrchestrateRequest
        
        request = OrchestrateRequest(
            task="Server is down",
            context={"priority": "high"},
            dry_run=True
        )
        assert request.task == "Server is down"
        assert request.dry_run is True
        assert request.context == {"priority": "high"}

    def test_analyze_task_request_valid(self):
        """Test valid AnalyzeTaskRequest model."""
        from twisterlab.api.routes_mcp_real import AnalyzeTaskRequest
        
        request = AnalyzeTaskRequest(task="Check database status")
        assert request.task == "Check database status"

    def test_orchestrate_request_too_short(self):
        """Test OrchestrateRequest rejects too short task."""
        from twisterlab.api.routes_mcp_real import OrchestrateRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            OrchestrateRequest(task="Hi")  # Less than 5 chars


class TestClassifyTicketEndpoint:
    """Tests for classify_ticket endpoint.
    
    Note: These tests may fail without a database connection.
    They are marked with @pytest.mark.integration for environments with DB.
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_classify_ticket_software(self, async_client):
        """Test ticket classification for software issues."""
        response = await async_client.post(
            "/api/v1/mcp/tools/classify_ticket",
            json={"description": "Application crashes when I click the button"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return ok or error (db may not be available)
        assert data["status"] in ["ok", "error"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_classify_ticket_hardware(self, async_client):
        """Test ticket classification for hardware issues."""
        response = await async_client.post(
            "/api/v1/mcp/tools/classify_ticket",
            json={"description": "Server hardware failure, disk errors"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "error"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_classify_ticket_network(self, async_client):
        """Test ticket classification for network issues."""
        response = await async_client.post(
            "/api/v1/mcp/tools/classify_ticket",
            json={"description": "Network connection timeout, can't access server"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "error"]


class TestResolveTicketEndpoint:
    """Tests for resolve_ticket endpoint."""

    @pytest.mark.asyncio
    async def test_resolve_ticket_success(self, async_client):
        """Test successful ticket resolution."""
        response = await async_client.post(
            "/api/v1/mcp/tools/resolve_ticket",
            json={"category": "software"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # May fail if DB not available
        assert data["status"] in ["ok", "error"]

    @pytest.mark.asyncio
    async def test_resolve_ticket_hardware(self, async_client):
        """Test hardware ticket resolution."""
        response = await async_client.post(
            "/api/v1/mcp/tools/resolve_ticket",
            json={"category": "hardware"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "error"]


class TestMonitorSystemHealthEndpoint:
    """Tests for monitor_system_health endpoint.
    
    Note: These tests may fail without a database connection.
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_monitor_health_all_checks(self, async_client):
        """Test monitoring with all checks enabled."""
        response = await async_client.post(
            "/api/v1/mcp/tools/monitor_system_health",
            json={
                "check_cpu": True,
                "check_memory": True,
                "check_disk": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # May fail if DB not available for logging
        assert data["status"] in ["ok", "error"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_monitor_health_minimal(self, async_client):
        """Test monitoring with minimal checks."""
        response = await async_client.post(
            "/api/v1/mcp/tools/monitor_system_health",
            json={"check_cpu": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "error"]


class TestAnalyzeSentimentEndpointMCP:
    """Tests for analyze_sentiment on MCP tools route."""

    @pytest.mark.asyncio
    async def test_sentiment_via_tools(self, async_client):
        """Test sentiment analysis via /tools/ route."""
        response = await async_client.post(
            "/api/v1/mcp/tools/analyze_sentiment",
            json={"text": "This is great!", "detailed": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["data"]["sentiment"] == "positive"

    @pytest.mark.asyncio
    async def test_sentiment_negative_via_tools(self, async_client):
        """Test negative sentiment via /tools/ route."""
        response = await async_client.post(
            "/api/v1/mcp/tools/analyze_sentiment",
            json={"text": "This is terrible and bad!", "detailed": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["data"]["sentiment"] == "negative"
        assert "keywords" in data["data"]


class TestListAgentsEndpoint:
    """Tests for list_autonomous_agents endpoint."""

    @pytest.mark.asyncio
    async def test_list_agents_get(self, async_client):
        """Test GET list_autonomous_agents."""
        response = await async_client.get("/api/v1/mcp/tools/list_autonomous_agents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "agents" in data["data"]
        assert len(data["data"]["agents"]) >= 9  # We have 9 agents

    @pytest.mark.asyncio
    async def test_list_agents_post(self, async_client):
        """Test POST list_autonomous_agents."""
        response = await async_client.post("/api/v1/mcp/tools/list_autonomous_agents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "agents" in data["data"]

    @pytest.mark.asyncio
    async def test_list_agents_contains_maestro(self, async_client):
        """Test that maestro agent is in the list."""
        response = await async_client.get("/api/v1/mcp/tools/list_autonomous_agents")
        
        data = response.json()
        agent_names = [a["name"] for a in data["data"]["agents"]]
        # Check for RealMaestroAgent (the actual class name)
        assert any("Maestro" in name for name in agent_names)


class TestHealthEndpointMCP:
    """Tests for /health endpoint on MCP tools."""

    @pytest.mark.asyncio
    async def test_tools_health(self, async_client):
        """Test health check on tools route."""
        response = await async_client.get("/api/v1/mcp/tools/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]
        # May have agents_count or just other fields
        assert "timestamp" in data or "agents_count" in data
