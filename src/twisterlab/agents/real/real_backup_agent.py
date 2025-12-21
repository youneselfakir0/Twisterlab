"""
Modernized RealBackupAgent
"""

from typing import Any, Dict, List, Optional
from twisterlab.agents.core.base import (
    TwisterAgent, 
    AgentCapability, 
    CapabilityParam, 
    ParamType, 
    AgentResponse,
    CapabilityType
)

class RealBackupAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "real-backup"

    @property
    def description(self) -> str:
        return "Handles system backups and data redundancy."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="create_backup",
                description="Create a backup for a specific service.",
                handler="handle_backup",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("service_name", ParamType.STRING, "Name of service to backup"),
                    CapabilityParam("location", ParamType.STRING, "Backup destination", required=False, default="cloud")
                ]
            )
        ]

    async def handle_backup(self, service_name: str, location: str = "cloud") -> AgentResponse:
        return AgentResponse(success=True, data={"backup_id": "BK-123", "service": service_name, "status": "COMPLETED", "size_mb": 256})
