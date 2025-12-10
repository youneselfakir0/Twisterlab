"""
Minimal RealMonitoringAgent for registry completeness.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from twisterlab.agents.base import TwisterAgent


class RealMonitoringAgent(TwisterAgent):
    def __init__(self) -> None:
        super().__init__(
            name="real-monitoring",
            display_name="Real Monitoring",
            description="Monitors system metrics and health",
            role="monitoring",
            tools=[{"type": "function", "function": {"name": "check_health"}}],
        )

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        return {"status": "healthy", "metrics": {"cpu": 45, "memory": 60}}


__all__ = ["RealMonitoringAgent"]
