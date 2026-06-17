"""
RealOdysseusAgent - AI Workspace Agent 🌌

This agent interfaces with the Odysseus AI Workspace (by pewdiepie-archdaemon)
to provide advanced chat and reasoning capabilities.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)

class RealOdysseusAgent(TwisterAgent):
    """
    Agent for interacting with Odysseus AI Workspace.
    """

    def __init__(self) -> None:
        super().__init__()
        # Get Odysseus service URL from environment or default to the remote server IP
        # L'adresse IP du serveur Ubuntu EDGESERVER-OPS est 192.168.0.30
        self._base_url = os.getenv("ODYSSEUS_URL", "http://192.168.0.30:7000")
        self._api_token = os.getenv("ODYSSEUS_API_TOKEN", "")
        logger.info(f"✅ RealOdysseusAgent initialized with base URL: {self._base_url}")

    @property
    def name(self) -> str:
        return "real-odysseus"

    @property
    def description(self) -> str:
        return "Interfaces with the Odysseus AI Workspace for chat and reasoning."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="chat",
                description="Send a message to Odysseus AI and get a response.",
                handler="chat",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        name="message",
                        param_type=ParamType.STRING,
                        description="The message to send to the AI.",
                        required=True,
                    ),
                    CapabilityParam(
                        name="model",
                        param_type=ParamType.STRING,
                        description="The model to use (optional).",
                        required=False,
                    ),
                    CapabilityParam(
                        name="session_id",
                        param_type=ParamType.STRING,
                        description="Optional session ID to resume a conversation.",
                        required=False,
                    ),
                ],
            ),
            AgentCapability(
                name="optimize_gene",
                description="Optimizes a protein or DNA sequence for a specific host organism.",
                handler="optimize_gene",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        name="sequence",
                        param_type=ParamType.STRING,
                        description="The DNA/Protein sequence to optimize.",
                        required=True,
                    ),
                    CapabilityParam(
                        name="organism",
                        param_type=ParamType.STRING,
                        description="Target host organism (e.g., E. coli, H. sapiens).",
                        required=False,
                        default="E. coli"
                    ),
                ],
            )
        ]

    async def execute(self, capability: str, params: Dict[str, Any]) -> AgentResponse:
        if capability == "chat":
            return await self.chat(
                message=params.get("message"),
                model=params.get("model"),
                session_id=params.get("session_id"),
            )
        elif capability == "optimize_gene":
            sequence = params.get("sequence")
            organism = params.get("organism", "E. coli")
            prompt = f"Optimize the following gene sequence for {organism}: {sequence}"
            return await self.chat(message=prompt)
        
        return AgentResponse(success=False, error=f"Capability '{capability}' not supported by {self.name}")

    async def chat(
        self, message: str, model: Optional[str] = None, session_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Calls Odysseus Sync Chat API.
        """
        logger.info(f"💬 Sending message to Odysseus: {message[:50]}...")
        
        if not self._api_token:
            return AgentResponse(success=False, error="ODYSSEUS_API_TOKEN not configured.")

        try:
            payload = {
                "message": message,
                "model": model or "auto",
                "session": session_id,
            }
            
            headers = {
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json",
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self._base_url}/api/v1/chat",
                    json=payload,
                    headers=headers
                )
                
            if response.status_code != 200:
                return AgentResponse(success=False, error=f"Odysseus API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return AgentResponse(
                success=True,
                data=data,
                metadata={"message": f"Received response from Odysseus using model {data.get('model')}."}
            )
            
        except Exception as e:
            logger.error(f"Error in Odysseus chat: {e}")
            return AgentResponse(success=False, error=f"Unexpected error: {str(e)}")
