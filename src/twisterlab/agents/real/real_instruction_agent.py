from __future__ import annotations

import logging
from typing import List

from twisterlab.agents.core.base import (
    CoreAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


class RealInstructionAgent(CoreAgent):
    """Instruction Agent - Parses and analyzes project instructions."""

    @property
    def name(self) -> str:
        return "instruction"

    @property
    def description(self) -> str:
        return "Processes and analyzes project instructions and documentation."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="parse_instructions",
                description="Parse and analyze instructions",
                handler="handle_parse_instructions",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("instruction_text", ParamType.STRING, "Text to parse", required=True),
                ],
            )
        ]

    async def handle_parse_instructions(self, instruction_text: str) -> AgentResponse:
        logger.info(f"Parsing instructions: {instruction_text[:50]}...")
        return AgentResponse(
            success=True, 
            data={
                "parsed": True, 
                "length": len(instruction_text), 
                "summary": "Instruction parsed successfully."
            }
        )
