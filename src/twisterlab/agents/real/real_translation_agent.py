"""
RealTranslationAgent - Multi-lingual translation powered by Cortex AI.
"""

"""
RealTranslationAgent - Multi-lingual translation powered by Cortex AI.
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


class RealTranslationAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "translation"

    @property
    def description(self) -> str:
        return "Translates text across multiple languages using Cortex AI."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="translate_text",
                description="Translates the source text to the target language.",
                handler="handle_translate",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("text", ParamType.STRING, "The text to translate", required=True),
                    CapabilityParam("target_language", ParamType.STRING, "The language to translate to (e.g., 'french', 'spanish', 'english')", required=True),
                    CapabilityParam("source_language", ParamType.STRING, "The auto-detected or specified source language", required=False)
                ]
            ),
            AgentCapability(
                name="translate",
                description="Alias for translate_text.",
                handler="handle_translate",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("text", ParamType.STRING, "The text to translate", required=True),
                    CapabilityParam("target_language", ParamType.STRING, "Dest language", required=True),
                ]
            )
        ]

    async def handle_translate(self, text: str, target_language: str, source_language: str = "auto") -> AgentResponse:
        from twisterlab.services.cortex import CortexClient
        client = CortexClient()
        
        system_prompt = PromptLoader.get("translator_expert", target_language=target_language, source_language=source_language)
        full_prompt = f"{system_prompt}\n\nTEXT TO TRANSLATE:\n{text}"

        response = await client.generate(prompt=full_prompt, model="llama3.2:1b")
            "translated_text": response.text.strip(),
            "target_language": target_language
        })

__all__ = ["RealTranslationAgent"]
