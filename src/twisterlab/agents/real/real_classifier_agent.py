"""
Modernized RealClassifierAgent
"""

from typing import List
from twisterlab.agents.core.base import (
    TwisterAgent, 
    AgentCapability, 
    CapabilityParam, 
    ParamType, 
    AgentResponse,
    CapabilityType
)

class RealClassifierAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "real-classifier"

    @property
    def description(self) -> str:
        return "Classifies incoming text or tickets into predefined categories."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="classify_ticket",
                description="Classify a ticket based on its text.",
                handler="handle_classify",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("ticket_text", ParamType.STRING, "The text of the ticket", required=True)
                ]
            )
        ]

    async def handle_classify(self, ticket_text: str) -> AgentResponse:
        """Simple classification logic."""
        text = ticket_text.lower()
        
        # Priority detection
        priority = "medium"
        if any(word in text for word in ["urgent", "critical", "emergency", "asap", "down"]):
            priority = "high"
        elif any(word in text for word in ["when you can", "low priority", "minor"]):
            priority = "low"
        
        # Category detection
        if any(word in text for word in ["database", "sql", "query", "postgres", "mysql", "db"]):
            category = "DATABASE"
        elif any(word in text for word in ["slow", "performance", "latency", "timeout"]):
            category = "PERFORMANCE"
        elif any(word in text for word in ["password", "login", "auth", "access", "permission"]):
            category = "ACCESS"
        elif any(word in text for word in ["software", "install", "update", "version"]):
            category = "SOFTWARE"
        elif any(word in text for word in ["bug", "error", "crash", "exception", "fail"]):
            category = "TECHNICAL"
        elif any(word in text for word in ["security", "breach", "hack", "vulnerability"]):
            category = "SECURITY"
        elif any(word in text for word in ["network", "connection", "dns", "firewall"]):
            category = "NETWORK"
        else:
            category = "GENERAL"
            
        return AgentResponse(success=True, data={"category": category, "priority": priority})
