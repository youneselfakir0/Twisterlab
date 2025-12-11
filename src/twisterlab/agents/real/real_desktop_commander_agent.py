"""
Minimal RealDesktopCommanderAgent for demo and tests.

This agent wraps the DesktopCommander features required by the API and
provides a simple execute contract to simulate command execution on a
remote machine. Keep this lightweight – it can be replaced later with a
full-featured implementation that actually executes commands securely.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from twisterlab.agents.base import TwisterAgent


@dataclass
class CommandStatus:
    status: str
    exit_code: int = 0
    output: Optional[str] = None
    error: Optional[str] = None


class RealDesktopCommanderAgent(TwisterAgent):
    def __init__(self) -> None:
        super().__init__(
            name="real-desktop-commander",
            display_name="Real Desktop Commander",
            description="Executes system-level commands on registered endpoints",
            role="desktop-commander",
            instructions="Execute commands from a restricted whitelist and return output",
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "execute_command",
                        "description": "Execute a command on a registered endpoint",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "device_id": {"type": "string"},
                                "command": {"type": "string"},
                                "timeout": {"type": "integer"},
                            },
                            "required": ["device_id", "command"],
                        },
                    },
                }
            ],
            model="llama-3.2",
            temperature=0.1,
        )

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        # Simulate a safe command execution – do not execute arbitrary shell
        # commands in tests. Return a CommandStatus-like dict for compatibility.
        status = CommandStatus(
            status="completed", exit_code=0, output=f"Executed: {task}"
        )
        return asdict(status)


__all__ = ["RealDesktopCommanderAgent", "CommandStatus"]
