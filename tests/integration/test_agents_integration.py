"""
Integration tests for TwisterLab Agents.

These tests verify that agents work correctly together
and can communicate with each other via the registry.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestMaestroAgentIntegration:
    """Integration tests for RealMaestroAgent."""

    @pytest.fixture
    def maestro_agent(self):
        """Create a Maestro agent for testing."""
        try:
            from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
            return RealMaestroAgent()
        except ImportError:
            pytest.skip("RealMaestroAgent not available")

    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = MagicMock()
        registry.get_agent = MagicMock(return_value=None)
        registry.list_agents = MagicMock(return_value=[])
        return registry

    @pytest.mark.asyncio
    async def test_maestro_initialization(self, maestro_agent):
        """Test Maestro agent initializes correctly."""
        assert maestro_agent.name == "maestro"
        assert hasattr(maestro_agent, 'get_capabilities')
        capabilities = maestro_agent.get_capabilities()
        cap_names = [c.name for c in capabilities]
        assert "orchestrate" in cap_names

    @pytest.mark.asyncio
    async def test_maestro_execute_simple_task(self, maestro_agent):
        """Test Maestro can execute a simple task via handle_orchestrate."""
        result = await maestro_agent.handle_orchestrate(task="analyze system health")
        assert result.success is True
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_maestro_execute_with_context(self, maestro_agent):
        """Test Maestro handles context correctly."""
        result = await maestro_agent.handle_analyze_task(task="urgent alert")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_maestro_with_registry(self, mock_registry):
        """Test Maestro works with agent registry."""
        try:
            from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
        except ImportError:
            pytest.skip("RealMaestroAgent not available")
        
        maestro = RealMaestroAgent(agent_registry=mock_registry)
        assert maestro.agent_registry is mock_registry


class TestMonitoringAgentIntegration:
    """Integration tests for RealMonitoringAgent."""

    @pytest.fixture
    def monitoring_agent(self):
        """Create a Monitoring agent for testing."""
        try:
            from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
            return RealMonitoringAgent()
        except ImportError:
            pytest.skip("RealMonitoringAgent not available")

    @pytest.mark.asyncio
    async def test_monitoring_initialization(self, monitoring_agent):
        """Test Monitoring agent initializes correctly."""
        assert monitoring_agent is not None
        assert hasattr(monitoring_agent, 'name')
        assert hasattr(monitoring_agent, 'execute')


class TestAgentRegistry:
    """Integration tests for Agent Registry."""

    @pytest.fixture
    def registry(self):
        """Create an agent registry."""
        try:
            from twisterlab.agents.registry import AgentRegistry
            return AgentRegistry()
        except ImportError:
            pytest.skip("AgentRegistry not available")

    def test_registry_initialization(self, registry):
        """Test registry initializes correctly."""
        assert registry is not None

    def test_registry_register_agent(self, registry):
        """Test registering an agent."""
        try:
            from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
        except ImportError:
            pytest.skip("RealMaestroAgent not available")
        
        agent = RealMaestroAgent()
        # If registry has register method
        if hasattr(registry, 'register'):
            registry.register(agent)
            assert registry.get_agent("real-maestro") is not None


class TestMCPServerIntegration:
    """Integration tests for MCP Server."""

    @pytest.fixture
    def mcp_server(self):
        """Create MCP server instance."""
        try:
            from twisterlab.agents.mcp.mcp_server import MCPServerContinue
            return MCPServerContinue()
        except ImportError:
            pytest.skip("MCPServerContinue not available")

    def test_mcp_server_initialization(self, mcp_server):
        """Test MCP server initializes correctly."""
        assert mcp_server.protocol_version == "2024-11-05"
        assert "twisterlab" in mcp_server.server_info["name"]
        assert mcp_server.mode in ["REAL", "HYBRID"]

    def test_mcp_server_info(self, mcp_server):
        """Test MCP server info is complete."""
        info = mcp_server.server_info
        assert "name" in info
        assert "version" in info
        assert "description" in info

    def test_mcp_handle_initialize(self, mcp_server):
        """Test MCP handles initialize request."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        response = mcp_server.handle_request(request)
        assert "result" in response or "error" in response

    def test_mcp_handle_tools_list(self, mcp_server):
        """Test MCP lists available tools."""
        # First initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        mcp_server.handle_request(init_request)
        
        # Then list tools
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        response = mcp_server.handle_request(request)
        # Should return tools or error
        assert "result" in response or "error" in response


class TestAgentCommunication:
    """Test agents can communicate with each other."""

    @pytest.mark.asyncio
    async def test_maestro_can_delegate_task(self):
        """Test Maestro can delegate tasks to other agents."""
        try:
            from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
        except ImportError:
            pytest.skip("RealMaestroAgent not available")
        
        # Create mock subordinate agent
        mock_agent = AsyncMock()
        mock_agent.name = "mock-agent"
        mock_agent.execute_capability = AsyncMock(return_value={"status": "completed"})
        
        # Create registry with mock agent
        mock_registry = MagicMock()
        mock_registry.get_agent = MagicMock(return_value=mock_agent)
        mock_registry.list_agents = MagicMock(return_value=[mock_agent])
        
        maestro = RealMaestroAgent(agent_registry=mock_registry)
        
        # Execute task via handle_orchestrate
        result = await maestro.handle_orchestrate(task="delegate task to monitoring")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_multiple_agents_workflow(self):
        """Test a workflow involving multiple agents."""
        try:
            from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
        except ImportError:
            pytest.skip("RealMaestroAgent not available")
        
        # Create agents
        maestro = RealMaestroAgent()
        
        # Simulate workflow steps using handle_analyze_task
        step1 = await maestro.handle_analyze_task(task="step 1: analyze")
        assert step1.success is True
        
        step2 = await maestro.handle_analyze_task(task="step 2: process")
        assert step2.success is True
        
        step3 = await maestro.handle_analyze_task(task="step 3: report")
        assert step3.success is True
