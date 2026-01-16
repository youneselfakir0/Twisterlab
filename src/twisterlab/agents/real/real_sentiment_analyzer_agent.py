"""
Sentiment Analyzer Agent (Modernized)

Uses NLP to determine text sentiment (Positive, Negative, Neutral).
"""

from typing import Any, Dict, List, Optional

from twisterlab.agents.core.base import (
    TwisterAgent, 
    AgentCapability, 
    CapabilityParam, 
    ParamType, 
    AgentResponse,
    CapabilityType
)

class SentimentAnalyzerAgent(TwisterAgent):
    """
    Agent specializing in sentiment analysis.
    Uses the modern TwisterAgent base class for optimal MCP integration.
    """

    @property
    def name(self) -> str:
        return "sentiment-analyzer"

    @property
    def description(self) -> str:
        return "Analyzes text sentiment and returns positive/negative/neutral classification."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="analyze_sentiment",
                description="Determine the sentiment of a given text.",
                handler="handle_analyze_sentiment",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("text", ParamType.STRING, "The text to analyze", required=True),
                    CapabilityParam("detailed", ParamType.BOOLEAN, "Whether to include keywords", required=False, default=False)
                ]
            )
        ]

    async def handle_analyze_sentiment(self, text: str, detailed: bool = False) -> AgentResponse:
        """Handler for sentiment analysis logic."""
        # Simulated logic (real NLP could be added here)
        text_lower = text.lower()
        
        positive_words = ["good", "great", "excellent", "amazing", "love", "fantastic", "resolved", "fixed", "working", "success"]
        negative_words = ["bad", "hate", "terrible", "catastrophic", "frustrated", "down", "slow", "urgent", "critical", 
                         "emergency", "error", "fail", "broken", "crash", "complaining", "issue", "problem", "not working"]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # Urgency detection
        is_urgent = any(word in text_lower for word in ["urgent", "critical", "emergency", "asap", "immediately"])
        
        if pos_count > neg_count:
            sentiment = "positive"
            confidence = min(0.5 + (pos_count * 0.1), 0.99)
        elif neg_count > pos_count or is_urgent:
            sentiment = "negative"
            confidence = min(0.5 + (neg_count * 0.1), 0.99)
            if is_urgent:
                confidence = max(confidence, 0.8)
        else:
            sentiment = "neutral"
            confidence = 0.5

        result = {
            "sentiment": sentiment,
            "confidence": round(confidence, 2),
            "text_length": len(text),
            "urgency": "high" if is_urgent else "normal"
        }
        
        if detailed:
            result["keywords"] = [w for w in positive_words + negative_words if w in text_lower]

        # Record metrics would happen here via router wrapping
        return AgentResponse(success=True, data=result)

    async def execute_legacy(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Keep compatibility with old API calls if needed."""
        detailed = context.get("detailed", False) if context else False
        res = await self.handle_analyze_sentiment(text=task, detailed=detailed)
        return res.data
