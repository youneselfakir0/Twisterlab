"""
CortexIAAgent - Invoke AI on 127.0.0.1:9090
"""
from __future__ import annotations
import logging
import os
from typing import List, Optional

try:
    import httpx
except ImportError:
    httpx = None

from twisterlab.agents.core.base import (
    CoreAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)
from twisterlab.agents.prompts.loader import PromptLoader

logger = logging.getLogger(__name__)


class CortexIAAgent(CoreAgent):
    """Call dedicated AI running on Cortex port 9090."""

    def __init__(self, registry=None) -> None:
        super().__init__(registry)
        from twisterlab.config.unified_settings import settings
        self._url = settings.infra.ollama_base_url
        self._model = settings.infra.ollama_model

    @property
    def name(self) -> str:
        return "cortex-ia"

    @property
    def description(self) -> str:
        return "Assistant IA du TwisterLab Mission Control"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="invoke_ia",
                description="Invoquer l'IA Cortex",
                handler="handle_invoke_ia",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("input", ParamType.STRING, "Le texte à traiter", required=True),
                    CapabilityParam("model", ParamType.STRING, "Modèle à utiliser", required=False),
                ],
                tags=["ia", "llm"]
            )
        ]

    async def handle_invoke_ia(self, input: str, model: Optional[str] = None) -> AgentResponse:
        """Handle AI invocation with flexible model support."""
        if not httpx:
            return AgentResponse(success=False, error="httpx non installé.")
        
        target_model = model or self._model
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Cortex IA -> Ollama: {target_model}")
                
                # Retrieve standardized system prompt from APMS repository
                system_prompt = PromptLoader.get("cortex_ia_main")
                
                # Standard /api/generate
                response = await client.post(
                    f"{self._url}/api/generate",
                    json={
                        "model": target_model, 
                        "prompt": f"{system_prompt}\n\nUtilisateur: {input}\nAssistant:", 
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    res_text = data.get("response", "").strip()
                    
                    # If it's raw JSON, try to clean it
                    if res_text.startswith("{") and "response" in res_text:
                        try:
                            import json
                            res_text = json.loads(res_text).get("response", res_text)
                        except: pass
                    
                    return AgentResponse(success=True, data=res_text)
                else:
                    return AgentResponse(success=False, error=f"Ollama error {response.status_code}: {response.text}")
                    
        except Exception as e:
            logger.error(f"Cortex IA Exception: {e}")
            return AgentResponse(success=False, error=f"Ollama Connection Failed: {str(e)}")


__all__ = ["CortexIAAgent"]
