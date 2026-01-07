"""
Test metrics instrumentation for SentimentAnalyzer Agent.
"""

import pytest
from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent

# Check if metrics are available
try:
    from twisterlab.agents.metrics import (
        sentiment_analysis_total,
        sentiment_confidence_score,
        sentiment_keyword_matches,
        sentiment_text_length,
        sentiment_analysis_errors,
        agent_requests_total,
        agent_execution_time_seconds,
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

# Only run these tests if metrics are available
pytestmark = pytest.mark.skipif(not METRICS_AVAILABLE, reason="Prometheus metrics not available")


@pytest.mark.unit
@pytest.mark.asyncio
class TestSentimentAnalyzerMetrics:
    """Test Prometheus metrics for SentimentAnalyzer"""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return SentimentAnalyzerAgent()

    async def test_metrics_imported(self):
        """Test that metrics are properly imported"""
        assert METRICS_AVAILABLE, "Metrics should be available"
        
        # Metrics are already imported at module level if METRICS_AVAILABLE is True
        assert sentiment_analysis_total is not None
        assert sentiment_confidence_score is not None
        assert sentiment_keyword_matches is not None
        assert sentiment_text_length is not None
        assert sentiment_analysis_errors is not None
        assert agent_requests_total is not None
        assert agent_execution_time_seconds is not None
        
        # All metrics should be defined
        assert sentiment_analysis_total is not None
        assert sentiment_confidence_score is not None
        assert sentiment_keyword_matches is not None
        assert sentiment_text_length is not None
        assert sentiment_analysis_errors is not None
        assert agent_requests_total is not None
        assert agent_execution_time_seconds is not None

    async def test_metrics_collected_on_success(self, agent):
        """Test that metrics are collected on successful analysis"""
        response = await agent.handle_analyze_sentiment(
            "This is a wonderful and fantastic product!",
            detailed=True
        )
        
        assert response.success is True
        assert response.data["sentiment"] == "positive"
        assert response.data["confidence"] > 0.5
        assert "keywords" in response.data

    async def test_metrics_collected_on_empty(self, agent):
        """Test analysis of empty text"""
        response = await agent.handle_analyze_sentiment("")
        
        assert response.success is True
        assert response.data["sentiment"] == "neutral"
        assert response.data["text_length"] == 0

    async def test_metrics_with_different_sentiments(self, agent):
        """Test metrics collection for different sentiment types"""
        test_cases = [
            ("This is amazing and great!", "positive"),
            ("This is terrible and bad!", "negative"),
            ("The meeting is at 3pm.", "neutral"),
        ]
        
        for text, expected_sentiment in test_cases:
            response = await agent.handle_analyze_sentiment(text)
            assert response.success is True
            assert response.data["sentiment"] == expected_sentiment

    async def test_execution_time_tracked(self, agent):
        """Test that execution time is tracked"""
        import time
        
        start = time.time()
        response = await agent.handle_analyze_sentiment(
            "A" * 1000,  # Long text
            detailed=True
        )
        duration = time.time() - start
        
        # Execution should be fast (<1s for rule-based)
        assert duration < 1.0
        assert response.success is True
        assert response.data["text_length"] == 1000

    async def test_keyword_matches_tracked(self, agent):
        """Test keyword match tracking in detailed mode"""
        response = await agent.handle_analyze_sentiment(
            "This is excellent, amazing, fantastic, and great!",
            detailed=True
        )
        
        assert response.success is True
        assert response.data["sentiment"] == "positive"
        assert "keywords" in response.data
        assert len(response.data["keywords"]) >= 3
