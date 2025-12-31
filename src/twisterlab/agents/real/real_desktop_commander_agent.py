"""
Minimal RealDesktopCommanderAgent for demo and tests.

This agent wraps the DesktopCommander features required by the API and
provides a simple execute contract to simulate command execution on a
remote machine.
"""

from __future__ import annotations

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

logger = logging.getLogger(__name__)


class RealDesktopCommanderAgent(TwisterAgent):
    """
    Executes system-level commands on registered endpoints.
    """

    @property
    def name(self) -> str:
        return "real-desktop-commander"

    @property
    def description(self) -> str:
        return "Executes system-level commands on registered endpoints"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="execute_command",
                description="Execute a command on a registered endpoint",
                handler="handle_execute_command",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        "device_id",
                        ParamType.STRING,
                        "Target device identifier",
                    ),
                    CapabilityParam(
                        "command",
                        ParamType.STRING,
                        "Command to execute",
                    ),
                    CapabilityParam(
                        "timeout",
                        ParamType.INTEGER,
                        "Execution timeout in seconds",
                        required=False,
                        default=30,
                    ),
                ],
                tags=["system", "desktop", "command"],
            )
        ]

    async def handle_execute_command(
        self, device_id: str, command: str, timeout: int = 30
    ) -> AgentResponse:
        """Execute a command."""
        # Simulation logic
        logger.info(f"Executing command on {device_id}: {command}")
        
        return AgentResponse(
            success=True,
            data={
                "status": "completed",
                "exit_code": 0,
                "output": f"Simulated execution of: {command} on {device_id}",
                "device_id": device_id
            }
        )


__all__ = ["RealDesktopCommanderAgent"]
