"""
Minimal RealResolverAgent implementation for the TwisterLab 'real' agent pack.

This file provides a small, test-friendly class that implements the
interface expected by the AgentRegistry. These are intentionally small and
simplified – they can be extended later with real logic (SOPs, tool calls,
and integrations).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from twisterlab.agents.base import TwisterAgent


class RealResolverAgent(TwisterAgent):
    """Simple resolver agent used for demos and tests.

    It implements the TwisterAgent.execute contract and returns a predictable
    response that makes automated tests deterministic.
    """

    def __init__(self) -> None:
        super().__init__(
            name="real-resolver",
            display_name="Real Resolver Agent",
            description="Resolves tickets using predefined SOPs",
            role="resolver",
            instructions="Resolve helpdesk tickets by following SOPs",
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "resolve_ticket",
                        "description": "Execute SOP step to resolve ticket",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                }
            ],
            model="deepseek-r1",
            temperature=0.2,
        )

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        # Simulate basic ticket processing
        return {"status": "resolved", "task": task, "detail": "Simulated resolution"}


__all__ = ["RealResolverAgent"]
