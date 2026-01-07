import pytest
from unittest.mock import MagicMock, patch

# Import conditionnel pour éviter les erreurs si les classes ne sont pas mockables facilement
with patch.dict("sys.modules", {
    "twisterlab.agents.real.real_classifier_agent": MagicMock(),
    "twisterlab.agents.real.real_resolver_agent": MagicMock(),
    "twisterlab.agents.real.real_monitoring_agent": MagicMock(),
    "twisterlab.agents.real.real_backup_agent": MagicMock(),
    "twisterlab.agents.real.real_sync_agent": MagicMock(),
    "twisterlab.agents.real.real_desktop_commander_agent": MagicMock(),
    "twisterlab.agents.real.real_maestro_agent": MagicMock(),
    "twisterlab.agents.real.browser_agent": MagicMock(),
    "twisterlab.agents.real.real_sentiment_analyzer_agent": MagicMock(),
}):
    from twisterlab.agents.registry import AgentRegistry

class TestAgentRegistry:
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Reset Singleton state before each test"""
        AgentRegistry._instance = None
        AgentRegistry._agents = {}

    @patch("twisterlab.agents.registry.RealClassifierAgent")
    @patch("twisterlab.agents.registry.RealResolverAgent")
    @patch("twisterlab.agents.registry.RealMonitoringAgent")
    @patch("twisterlab.agents.registry.RealBackupAgent")
    @patch("twisterlab.agents.registry.RealSyncAgent")
    @patch("twisterlab.agents.registry.RealDesktopCommanderAgent")
    @patch("twisterlab.agents.registry.RealMaestroAgent")
    @patch("twisterlab.agents.registry.RealBrowserAgent")
    @patch("twisterlab.agents.registry.SentimentAnalyzerAgent")
    def test_singleton_pattern(self, *mocks):
        """Ensure only one instance is created"""
        reg1 = AgentRegistry()
        reg2 = AgentRegistry()
        assert reg1 is reg2

    def test_get_agent_exact_match(self):
        """Test retrieving agent by exact name"""
        with patch.object(AgentRegistry, 'initialize_agents') as mock_init:
            registry = AgentRegistry()
            mock_agent = MagicMock()
            mock_agent.name = "TestAgent"
            registry._agents = {"testagent": mock_agent}
            
            assert registry.get_agent("testagent") == mock_agent
            assert registry.get_agent("TestAgent") == mock_agent

    def test_get_agent_fuzzy_match(self):
        """Test retrieving agent by fuzzy name matching"""
        with patch.object(AgentRegistry, 'initialize_agents') as mock_init:
            registry = AgentRegistry()
            mock_agent = MagicMock()
            mock_agent.name = "MonitoringAgent"
            registry._agents = {"monitoring": mock_agent}
            
            # Cases handled by normalizer logic
            assert registry.get_agent("monitoring-agent") == mock_agent
            assert registry.get_agent("monitoring_agent") == mock_agent
            
            # Cases handled by substring logic
            assert registry.get_agent("monitor") == mock_agent

    def test_get_agent_not_found(self):
        """Test looking for non-existent agent"""
        with patch.object(AgentRegistry, 'initialize_agents') as mock_init:
            registry = AgentRegistry()
            registry._agents = {}
            assert registry.get_agent("unknown_agent") is None
            assert registry.get_agent("") is None

    def test_list_agents(self):
        """Test listing agents returns correct structure"""
        with patch.object(AgentRegistry, 'initialize_agents') as mock_init:
            registry = AgentRegistry()
            mock_agent = MagicMock()
            mock_agent.agent_id = "123"
            mock_agent.name = "TestAgent"
            mock_agent.version = "1.0"
            mock_agent.description = "Test Desc"
            mock_agent.status.value = "idle"
            
            registry._agents = {"testagent": mock_agent}
            
            agents_list = registry.list_agents()
            assert "testagent" in agents_list
            assert agents_list["testagent"]["agent_id"] == "123"
            assert agents_list["testagent"]["status"] == "idle"
