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
