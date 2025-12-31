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
        if "password" in text or "login" in text:
            category = "ACCESS"
        elif "software" in text or "install" in text:
            category = "SOFTWARE"
        elif "bug" in text or "error" in text:
            category = "TECHNICAL"
        else:
            category = "GENERAL"
            
        return AgentResponse(success=True, data={"category": category, "priority": "medium"})
