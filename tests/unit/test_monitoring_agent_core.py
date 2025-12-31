import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from twisterlab.agents.core.monitoring import MonitoringAgent, AgentResponse

class TestMonitoringAgent:
    @pytest.fixture
    def agent(self):
        # Create agent and mock its registry dependency
        agent = MonitoringAgent()
        # registry is a read-only property returning _registry, so we mock _registry
        agent._registry = MagicMock()
        return agent

    def test_initialization(self, agent):
        assert agent.name == "monitoring"
        assert "monitoring" in agent.description.lower()
        capabilities = agent.get_capabilities()
        assert any(c.name == "health_check" for c in capabilities)
        assert any(c.name == "get_system_metrics" for c in capabilities)

    @pytest.mark.asyncio
    async def test_handle_get_system_metrics_success(self, agent):
        # Mock the system interface returned by registry
        mock_system = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.cpu_percent = 15.5
        mock_metrics.memory_percent = 50.0
        mock_metrics.memory_used_gb = 8.0
        mock_metrics.memory_total_gb = 16.0
        mock_metrics.disk_percent = 60.0
        mock_metrics.disk_used_gb = 40.0
        mock_metrics.disk_total_gb = 100.0
        mock_metrics.container_count = 5
        
        # Setup async return value
        mock_system.get_metrics = AsyncMock(return_value=mock_metrics)
        agent.registry.get_system.return_value = mock_system
        
        # Execute
        response = await agent.handle_get_system_metrics()
        
        # Verify
        assert response.success is True
        assert response.data["cpu_percent"] == 15.5
        assert response.data["memory_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_handle_health_check_healthy(self, agent):
        # Mock health check response
        mock_health_item = MagicMock()
        mock_health_item.status.value = "connected"
        mock_health_item.latency_ms = 10
        mock_health_item.message = "OK"
        mock_health_item.metadata = {}
        
        agent.registry.health_check_all = AsyncMock(return_value={
            "database": mock_health_item,
            "cache": mock_health_item
        })

        # Execute
        response = await agent.handle_health_check()
        
        # Verify
        assert response.success is True
        assert response.data["overall"] == "healthy"
        assert response.data["services"]["database"]["status"] == "connected"

    @pytest.mark.asyncio
    async def test_handle_list_containers(self, agent):
        mock_system = MagicMock()
        mock_container = MagicMock()
        mock_container.id = "abc"
        mock_container.name = "test-container"
        mock_container.image = "nginx"
        mock_container.state.value = "running"
        mock_container.ports = {"80/tcp": 8080}
        
        mock_system.list_containers = AsyncMock(return_value=[mock_container])
        agent.registry.get_system.return_value = mock_system
        
        response = await agent.handle_list_containers()
        
        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0]["name"] == "test-container"
