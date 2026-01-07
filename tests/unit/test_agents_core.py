"""
Unit tests for agent base classes and core functionality
Tests TwisterAgent, BaseAgent, and related core components
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Mark all tests as unit tests
pytestmark = pytest.mark.unit


class TestTwisterAgent:
    """Tests for TwisterAgent base class."""

    def test_agent_init(self):
        """Test TwisterAgent initialization."""
        from twisterlab.agents.base import TwisterAgent
        
        # Create a concrete implementation for testing
        class ConcreteAgent(TwisterAgent):
            async def execute(self, task, context=None):
                return {"result": task}
        
        agent = ConcreteAgent(
            name="test-agent",
            display_name="Test Agent",
            description="A test agent for unit testing"
        )
        
        assert agent.name == "test-agent"
        assert agent.display_name == "Test Agent"
        assert agent.description == "A test agent for unit testing"
        assert agent.role == "assistant"
        assert agent.model == "llama-3.2"
        assert agent.temperature == 0.7

    def test_agent_with_custom_params(self):
        """Test TwisterAgent with custom parameters."""
        from twisterlab.agents.base import TwisterAgent
        
        class ConcreteAgent(TwisterAgent):
            async def execute(self, task, context=None):
                return {"result": task}
        
        tools = [{"name": "tool1", "description": "A tool"}]
        metadata = {"version": "1.0"}
        
        agent = ConcreteAgent(
            name="custom-agent",
            display_name="Custom Agent",
            description="Custom agent",
            role="specialist",
            instructions="Custom instructions",
            tools=tools,
            model="gpt-4",
            temperature=0.5,
            metadata=metadata
        )
        
        assert agent.role == "specialist"
        assert agent.instructions == "Custom instructions"
        assert agent.tools == tools
        assert agent.model == "gpt-4"
        assert agent.temperature == 0.5
        assert agent.metadata == metadata

    @pytest.mark.asyncio
    async def test_agent_execute(self):
        """Test TwisterAgent execute method."""
        from twisterlab.agents.base import TwisterAgent
        
        class ConcreteAgent(TwisterAgent):
            async def execute(self, task, context=None):
                return {"result": task, "context": context}
        
        agent = ConcreteAgent(
            name="exec-agent",
            display_name="Exec Agent",
            description="Execution test"
        )
        
        result = await agent.execute("test task", {"key": "value"})
        assert result["result"] == "test task"
        assert result["context"]["key"] == "value"


class TestCoreAgent:
    """Tests for CoreAgent from agents/core/base.py."""

    def test_core_agent_capability(self):
        """Test AgentCapability dataclass."""
        from twisterlab.agents.core.base import AgentCapability
        
        capability = AgentCapability(
            name="test_capability",
            description="A test capability",
            handler="handle_test"
        )
        
        assert capability.name == "test_capability"
        assert capability.description == "A test capability"
        assert capability.handler == "handle_test"

    def test_agent_response_success(self):
        """Test AgentResponse model with success."""
        from twisterlab.agents.core.base import AgentResponse
        
        response = AgentResponse(success=True, data={"key": "value"})
        assert response.success is True
        assert response.data["key"] == "value"

    def test_agent_response_error(self):
        """Test AgentResponse with error."""
        from twisterlab.agents.core.base import AgentResponse
        
        response = AgentResponse(success=False, error="Something failed")
        assert response.success is False
        assert response.error == "Something failed"


class TestRealAgents:
    """Tests for real agent implementations."""

    def test_classifier_agent_init(self):
        """Test RealClassifierAgent initialization."""
        from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
        
        agent = RealClassifierAgent()
        assert agent.name == "real-classifier"
        # Uses handle_classify via execute(), not direct method
        assert hasattr(agent, "handle_classify")

    def test_resolver_agent_init(self):
        """Test RealResolverAgent initialization."""
        from twisterlab.agents.real.real_resolver_agent import RealResolverAgent
        
        agent = RealResolverAgent()
        assert agent.name == "real-resolver"
        # Uses handle_resolve via execute(), not direct method
        assert hasattr(agent, "handle_resolve")

    def test_monitoring_agent_init(self):
        """Test RealMonitoringAgent initialization."""
        from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
        
        agent = RealMonitoringAgent()
        assert agent.name == "real-monitoring"

    def test_backup_agent_init(self):
        """Test RealBackupAgent initialization."""
        from twisterlab.agents.real.real_backup_agent import RealBackupAgent
        
        agent = RealBackupAgent()
        assert agent.name == "real-backup"

    def test_sentiment_analyzer_init(self):
        """Test SentimentAnalyzerAgent initialization."""
        from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
        
        agent = SentimentAnalyzerAgent()
        assert agent.name == "sentiment-analyzer"

    @pytest.mark.asyncio
    async def test_classifier_classify(self):
        """Test classifier agent classification via execute."""
        from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
        
        agent = RealClassifierAgent()
        result = await agent.execute("classify_ticket", ticket_text="My computer won't turn on")
        
        assert result.success
        assert "category" in result.data
        assert "priority" in result.data

    @pytest.mark.asyncio
    async def test_sentiment_analyze(self):
        """Test sentiment analyzer via execute method."""
        from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
        
        agent = SentimentAnalyzerAgent()
        result = await agent.execute("analyze_sentiment", text="I love this product!")
        
        assert result.success
        assert "sentiment" in result.data
        assert result.data["sentiment"] in ["positive", "negative", "neutral"]
