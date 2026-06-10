import logging
from typing import List

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)
from twisterlab.agents.core.openclaw_tool import OpenClawTool

logger = logging.getLogger(__name__)

class OpenClawAgent(TwisterAgent):
    """
    OpenClaw agent wrapper. Exposes OpenClaw capabilities via the MCP server.
    """

    def __init__(self, service_registry=None):
        super().__init__(service_registry)
        self.openclaw = OpenClawTool(session_id="mcp_default")
        logger.info("🦞 OpenClawAgent initialized")

    @property
    def name(self) -> str:
        return "openclaw"

    @property
    def description(self) -> str:
        return "An autonomous browser agent powered by OpenClaw. Can browse the web, interact with web pages, and extract structured data."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="web_browser_action",
                description="Use the OpenClaw autonomous browser agent to perform actions on the web.",
                handler="handle_web_action",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        "message",
                        ParamType.STRING,
                        "The instruction for the browser agent. E.g., 'Go to example.com and extract the title'",
                    ),
                    CapabilityParam(
                        "session_id",
                        ParamType.STRING,
                        "Optional session ID to maintain browser state (cookies, login). Defaults to 'mcp_default'",
                        required=False,
                        default="mcp_default"
                    )
                ],
                tags=["web", "browser", "automation", "openclaw"],
            )
        ]

    async def handle_web_action(self, message: str, session_id: str = "mcp_default") -> AgentResponse:
        try:
            import asyncio
            response = await asyncio.to_thread(self.openclaw.execute, message, session_id=session_id)
            
            if response.success:
                return AgentResponse(
                    success=True,
                    data={
                        "text": response.text,
                        "raw": response.raw_data,
                        "execution_time": response.execution_time
                    }
                )
            else:
                return AgentResponse(
                    success=False,
                    error=str(response.raw_data.get('error', 'Unknown error')),
                    data={"raw": response.raw_data}
                )
        except Exception as e:
            logger.error(f"OpenClaw execution failed: {e}")
            return AgentResponse(success=False, error=str(e))
