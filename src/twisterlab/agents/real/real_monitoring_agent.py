"""
RealMonitoringAgent - Real System Metrics Collection.
"""

from __future__ import annotations

import logging
import os
import platform
import socket
from datetime import datetime, timezone
from typing import List

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


class RealMonitoringAgent(TwisterAgent):
    def __init__(self) -> None:
        super().__init__()
        if PSUTIL_AVAILABLE:
            logger.info("RealMonitoringAgent initialized with psutil")

    @property
    def name(self) -> str:
        return "monitoring"

    @property
    def description(self) -> str:
        return "Collects real system metrics using psutil"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="collect_metrics",
                description="Collect all system metrics",
                handler="handle_collect_metrics",
                capability_type=CapabilityType.QUERY,
                params=[],
                tags=["monitoring"],
            ),
        ]

    async def handle_collect_metrics(self) -> AgentResponse:
        if not PSUTIL_AVAILABLE:
            return AgentResponse(success=True, data={"cpu": 45.0, "memory": 60.0, "simulated": True})
        
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "data_source": "psutil",
                "cpu": {
                    "usage_percent": cpu,
                    "cores": psutil.cpu_count(),
                },
                "memory": {
                    "total_gb": round(mem.total / (1024**3), 2),
                    "used_gb": round(mem.used / (1024**3), 2),
                    "percent_used": mem.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percent_used": disk.percent,
                },
            }
            return AgentResponse(success=True, data=data)
        except Exception as e:
            return AgentResponse(success=False, error=str(e))


__all__ = ["RealMonitoringAgent", "PSUTIL_AVAILABLE"]
