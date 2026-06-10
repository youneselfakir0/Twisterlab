"""
RealArchiveAgent v3.5.5
Handles automatic persistence of Maestro missions and Cortex chat sessions.
"""

import os
import json
from datetime import datetime, timezone
from typing import List
from twisterlab.agents.core.base import (
    TwisterAgent, 
    AgentCapability, 
    CapabilityParam, 
    ParamType, 
    AgentResponse,
    CapabilityType
)

import logging
logger = logging.getLogger(__name__)

class RealArchiveAgent(TwisterAgent):
    def __init__(self, registry=None):
        super().__init__(registry)
        # Fix base_dir relative to this file to avoid CWD issues
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Up 3 levels: real -> agents -> twisterlab -> src
        self.base_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", "archives"))
        self._ensure_dirs()
        logger.info(f"ArchiveAgent v3.5.6 initialized: {self.base_dir}")

    def _ensure_dirs(self):
        try:
            os.makedirs(os.path.join(self.base_dir, "missions"), exist_ok=True)
            os.makedirs(os.path.join(self.base_dir, "chat"), exist_ok=True)
            logger.info("Archive directories ensured.")
        except Exception as e:
            logger.error(f"Failed to create archive directories: {e}")

    @property
    def name(self) -> str:
        return "archive"

    @property
    def description(self) -> str:
        return "Handles automatic system data archival (Missions, Chat, Metrics)."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="archive_mission",
                description="Automatically archive a Maestro mission result.",
                handler="handle_archive_mission",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("mission_id", ParamType.STRING, "Unique ID of the mission"),
                    CapabilityParam("data", ParamType.OBJECT, "Mission objective and results")
                ]
            ),
            AgentCapability(
                name="archive_result",
                description="Alias for archive_mission.",
                handler="handle_archive_mission",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("mission_id", ParamType.STRING, "Unique ID of the mission", required=False),
                    CapabilityParam("data", ParamType.OBJECT, "Mission objective and results", required=False)
                ]
            ),
            AgentCapability(
                name="archive_chat",
                description="Backup a chat session to the server.",
                handler="handle_archive_chat",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("session_id", ParamType.STRING, "Unique session identifier"),
                    CapabilityParam("messages", ParamType.ARRAY, "List of chat message objects")
                ]
            ),
            AgentCapability(
                name="get_history",
                description="Retrieve recently archived mission summaries.",
                handler="handle_get_history",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("category", ParamType.STRING, "Archive category (missions/chat)", default="missions")
                ]
            )
        ]

    async def handle_archive_mission(self, mission_id: str = "AUTO", data: dict = None) -> AgentResponse:
        try:
            if not data:
                data = {"status": "partial_archive", "timestamp": datetime.now(timezone.utc).isoformat()}
            
            filename = f"mission_{mission_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.base_dir, "missions", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Mission {mission_id} archived to {filepath}")
            return AgentResponse(success=True, data={"filepath": filepath, "mission_id": mission_id})
        except Exception as e:
            logger.error(f"Error archiving mission {mission_id}: {e}")
            return AgentResponse(success=False, error=str(e))

    async def handle_archive_chat(self, session_id: str, messages: list) -> AgentResponse:
        try:
            filename = f"chat_{session_id}.json"
            filepath = os.path.join(self.base_dir, "chat", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "session_id": session_id, 
                    "last_update": datetime.now(timezone.utc).isoformat(), 
                    "messages": messages
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Chat session {session_id} backed up.")
            return AgentResponse(success=True, data={"filepath": filepath})
        except Exception as e:
            logger.error(f"Error backing up chat {session_id}: {e}")
            return AgentResponse(success=False, error=str(e))

    async def handle_get_history(self, category: str = "missions") -> AgentResponse:
        try:
            path = os.path.join(self.base_dir, category)
            if not os.path.exists(path):
                return AgentResponse(success=True, data={"category": category, "files": []})
                
            files = sorted(os.listdir(path), reverse=True)[:10]
            logger.info(f"Retrieved {len(files)} items for category {category}")
            return AgentResponse(success=True, data={"category": category, "files": files})
        except Exception as e:
            logger.error(f"Error getting history for {category}: {e}")
            return AgentResponse(success=False, error=str(e))
