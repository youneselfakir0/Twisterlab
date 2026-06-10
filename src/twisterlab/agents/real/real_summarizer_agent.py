"""
RealSummarizerAgent - Text summarization powered by Cortex AI.
"""

"""
RealSummarizerAgent - Text summarization powered by Cortex AI.
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
from twisterlab.agents.prompts.loader import PromptLoader


class RealSummarizerAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "summarizer"

    @property
    def description(self) -> str:
        return "Summarizes large text bodies into concise representations."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="summarize_text",
                description="Summarizes the source text.",
                handler="handle_summarize",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("text", ParamType.STRING, "The text to summarize", required=True),
                    CapabilityParam("length", ParamType.STRING, "Desired length: 'short', 'medium', or 'long'", required=False),
                    CapabilityParam("focus", ParamType.STRING, "Optional focus of the summary (e.g., 'technical', 'business')", required=False)
                ]
            ),
            AgentCapability(
                name="summarize",
                description="Alias for summarize_text.",
                handler="handle_summarize",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("text", ParamType.STRING, "The text to summarize", required=True),
                ]
            )
        ]

    async def handle_summarize(self, text: str, length: str = "medium", focus: str = "general") -> AgentResponse:
        from twisterlab.services.cortex import CortexClient
        client = CortexClient()
        
        system_prompt = PromptLoader.get("summarizer_basic", length=length, focus=focus)
        full_prompt = f"{system_prompt}\n\nTEXT TO SUMMARIZE:\n{text}"

        response = await client.generate(prompt=full_prompt, model="llama3.2:1b")
            "length_requested": length,
            "focus_requested": focus
        })

__all__ = ["RealSummarizerAgent"]
