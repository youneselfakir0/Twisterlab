from __future__ import annotations

import logging
import json
from typing import List, Optional, Dict, Any

try:
    import httpx
except ImportError:
    httpx = None

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


class N8nNavigatorAgent(TwisterAgent):
    """
    Web / Desktop Navigator Agent powered by n8n.
    Allows triggering webhooks and workflows dynamically.
    """

    def __init__(self, registry=None) -> None:
        super().__init__(registry)
        self._url = "http://192.168.0.30:5678"

    @property
    def name(self) -> str:
        return "web-desktop-navigator"

    @property
    def description(self) -> str:
        return "Web & Desktop Navigator Agent powered by n8n (192.168.0.30:5678) to automate browser tasks, API workflows, and desktop webhooks"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="n8n_status",
                description="Check the connection and status of the n8n backend engine",
                handler="handle_n8n_status",
                capability_type=CapabilityType.QUERY,
                params=[],
                tags=["navigator", "n8n", "status"],
            ),
            AgentCapability(
                name="n8n_trigger_webhook",
                description="Trigger an automation workflow via Webhook",
                handler="handle_trigger_webhook",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        "webhook_path",
                        ParamType.STRING,
                        "Path to the webhook (e.g. 'my-automation')",
                        required=True,
                    ),
                    CapabilityParam(
                        "method",
                        ParamType.STRING,
                        "HTTP method ('GET' or 'POST')",
                        required=False,
                        default="POST",
                    ),
                    CapabilityParam(
                        "payload",
                        ParamType.STRING,
                        "JSON string containing the payload to push to n8n",
                        required=False,
                        default="{}",
                    ),
                ],
                tags=["navigator", "n8n", "webhook", "automation"],
            ),
        ]

    async def handle_n8n_status(self) -> AgentResponse:
        """Check if n8n is alive."""
        if not httpx:
            return AgentResponse(success=False, error="httpx not installed.")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self._url}/healthz")
                if res.status_code == 200:
                    return AgentResponse(
                        success=True,
                        data={
                            "message": "N8N Navigator Engine is ONLINE",
                            "status": res.json() if res.headers.get("content-type") == "application/json" else res.text,
                            "url": self._url
                        }
                    )
                else:
                    return AgentResponse(success=False, error=f"Status code {res.status_code}")
        except Exception as e:
            logger.error(f"N8N connection error: {e}")
            return AgentResponse(success=False, error=f"Could not reach n8n server at {self._url}: {str(e)}")

    async def handle_trigger_webhook(self, webhook_path: str, method: str = "POST", payload: str = "{}") -> AgentResponse:
        """Trigger an n8n webhook to launch an automation navigator workflow."""
        if not httpx:
            return AgentResponse(success=False, error="httpx not installed.")
            
        try:
            parsed_payload = json.loads(payload)
        except json.JSONDecodeError:
            return AgentResponse(success=False, error="Payload must be a valid JSON string.")
            
        webhook_url = f"{self._url}/webhook/{webhook_path}"
        if method.upper() not in ("GET", "POST", "PUT", "DELETE"):
             method = "POST"
             
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if method.upper() == "GET":
                    res = await client.get(webhook_url, params=parsed_payload)
                else:
                    res = await client.request(method.upper(), webhook_url, json=parsed_payload)
                    
                if 200 <= res.status_code < 300:
                    try:
                        resp_data = res.json()
                    except:
                        resp_data = res.text
                    return AgentResponse(success=True, data={
                        "message": "Webhook executed successfully",
                        "response": resp_data
                    })
                else:
                    return AgentResponse(success=False, error=f"n8n Webhook returned error: {res.status_code} - {res.text}")
                    
        except Exception as e:
            logger.error(f"N8N webhook execution error: {e}")
            return AgentResponse(success=False, error=f"Failed to execute webhook at {webhook_url}: {str(e)}")

__all__ = ["N8nNavigatorAgent"]
