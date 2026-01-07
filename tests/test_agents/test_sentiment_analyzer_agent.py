"""
Unit tests for SentimentAnalyzerAgent.
"""

import pytest
from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent


@pytest.mark.unit
@pytest.mark.asyncio
class TestSentimentAnalyzerAgent:
    """Test suite for SentimentAnalyzerAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return SentimentAnalyzerAgent()

    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "sentiment-analyzer"
        assert "sentiment" in agent.description.lower()

    async def test_positive_sentiment(self, agent):
        """Test detection of positive sentiment."""
        response = await agent.handle_analyze_sentiment(
            "This is an excellent and amazing product! I love it!"
        )
        
        assert response.success is True
        assert response.data["sentiment"] == "positive"
        assert response.data["confidence"] > 0.5
        assert "text_length" in response.data

    async def test_negative_sentiment(self, agent):
        """Test detection of negative sentiment."""
        response = await agent.handle_analyze_sentiment(
            "This is terrible and bad. I hate it completely."
        )
        
        assert response.success is True
        assert response.data["sentiment"] == "negative"
        assert response.data["confidence"] > 0.5

    async def test_neutral_sentiment(self, agent):
        """Test detection of neutral sentiment."""
        response = await agent.handle_analyze_sentiment(
            "The product was delivered on Tuesday."
        )
        
        assert response.success is True
        assert response.data["sentiment"] == "neutral"
        assert response.data["confidence"] == 0.5

    async def test_empty_text(self, agent):
        """Test handling of empty text."""
        response = await agent.handle_analyze_sentiment("")
        
        assert response.success is True
        assert response.data["sentiment"] == "neutral"
        assert response.data["text_length"] == 0

    async def test_detailed_analysis(self, agent):
        """Test detailed mode returns keywords."""
        response = await agent.handle_analyze_sentiment(
            "This is great and excellent!",
            detailed=True
        )
        
        assert response.success is True
        assert "keywords" in response.data
        assert "great" in response.data["keywords"]
        assert "excellent" in response.data["keywords"]

    async def test_no_keywords_without_detailed(self, agent):
        """Test keywords not returned without detailed flag."""
        response = await agent.handle_analyze_sentiment(
            "This is great and excellent!",
            detailed=False
        )
        
        assert response.success is True
        assert "keywords" not in response.data

    async def test_capabilities(self, agent):
        """Test agent has analyze_sentiment capability."""
        caps = agent.get_capabilities()
        cap_names = [c.name for c in caps]
        assert "analyze_sentiment" in cap_names

    async def test_capability_params(self, agent):
        """Test capability has correct parameters."""
        caps = agent.get_capabilities()
        analyze_cap = next(c for c in caps if c.name == "analyze_sentiment")
        
        param_names = [p.name for p in analyze_cap.params]
        assert "text" in param_names
        assert "detailed" in param_names

    async def test_mixed_sentiment(self, agent):
        """Test text with both positive and negative words."""
        response = await agent.handle_analyze_sentiment(
            "This is great but also terrible",
            detailed=True
        )
        
        assert response.success is True
        # Equal positive/negative should be neutral
        assert response.data["sentiment"] == "neutral"
        assert "great" in response.data["keywords"]
        assert "terrible" in response.data["keywords"]

    async def test_confidence_scaling(self, agent):
        """Test confidence increases with more sentiment words."""
        response1 = await agent.handle_analyze_sentiment("good")
        response2 = await agent.handle_analyze_sentiment("good great excellent amazing")
        
        assert response2.data["confidence"] > response1.data["confidence"]

    async def test_case_insensitive(self, agent):
        """Test sentiment detection is case insensitive."""
        response = await agent.handle_analyze_sentiment("EXCELLENT AMAZING GREAT")
        
        assert response.success is True
        assert response.data["sentiment"] == "positive"
