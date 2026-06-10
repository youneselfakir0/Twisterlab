"""
InvokeAIAgent - Invoke AI Image Generation on 192.168.0.20:9090
"""
from __future__ import annotations
import logging
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

logger = logging.getLogger(__name__)

class InvokeAIAgent(CoreAgent):
    """Call dedicated InvokeAI server running on 127.0.0.1:9092."""

    def __init__(self, registry=None) -> None:
        super().__init__(registry)
        self._url = "http://127.0.0.1:9092"

    @property
    def name(self) -> str:
        return "invoke-ai"

    @property
    def description(self) -> str:
        return "Interact with InvokeAI server for image generation and status (127.0.0.1:9092)"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="get_status",
                description="Get the status and version of the InvokeAI server",
                handler="handle_get_status",
                capability_type=CapabilityType.QUERY,
                params=[],
                tags=["ia", "invokeai", "status"]
            ),
            AgentCapability(
                name="list_models",
                description="List available models in InvokeAI",
                handler="handle_list_models",
                capability_type=CapabilityType.QUERY,
                params=[],
                tags=["ia", "invokeai", "models"]
            ),
            AgentCapability(
                name="generate_image",
                description="Enqueue an image generation task on InvokeAI",
                handler="handle_generate_image",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("prompt", ParamType.STRING, "Your positive image prompt", required=True),
                    CapabilityParam("negative_prompt", ParamType.STRING, "Your negative image prompt", required=False),
                    CapabilityParam("model", ParamType.STRING, "Model name (optional)", required=False),
                    CapabilityParam("steps", ParamType.INTEGER, "Sampling steps (optional, default 30)", required=False),
                ],
                tags=["ia", "invokeai", "image"]
            )
        ]

    async def _safe_get(self, endpoint: str) -> dict:
        if not httpx:
            return {"error": "httpx not installed"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self._url}{endpoint}")
                if resp.status_code == 200:
                    return {"success": True, "data": resp.json()}
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def handle_get_status(self) -> AgentResponse:
        v_res = await self._safe_get("/api/v1/app/version")
        q_res = await self._safe_get("/api/v1/queue/b/status")
        
        if not v_res.get("success") and not q_res.get("success"):
            return AgentResponse(success=False, error=f"Could not connect to InvokeAI at {self._url}")
            
        return AgentResponse(success=True, data={
            "server": self._url,
            "version": v_res.get("data", {}).get("version", "unknown") if v_res.get("success") else "error",
            "queue_status": q_res.get("data", {}) if q_res.get("success") else "error"
        })

    async def handle_list_models(self) -> AgentResponse:
        models_res = await self._safe_get("/api/v2/models/")  # InvokeAI typically uses v2 for models now
        if not models_res.get("success"):
            models_res = await self._safe_get("/api/v1/models/") # Fallback to v1
            
        if not models_res.get("success"):
            return AgentResponse(success=False, error=models_res.get("error"))
            
        return AgentResponse(success=True, data=models_res.get("data", {}))

    async def handle_generate_image(self, prompt: str, negative_prompt: Optional[str] = None, model: Optional[str] = None, steps: Optional[int] = 30) -> AgentResponse:
        if not httpx:
            return AgentResponse(success=False, error="httpx not installed on the server.")
            
        try:
            # 1. Fetch the most recent item from the queue to clone its graph structure
            q_res = await self._safe_get("/api/v1/queue/default/list_all")
            
            if not q_res.get("success") or not isinstance(q_res.get("data"), list) or len(q_res["data"]) == 0:
                return AgentResponse(success=False, error="No previous generations found in the InvokeAI queue to use as a graph template. Please run at least one generation from the web UI first.")
                
            last_item = q_res["data"][-1]  # Get the MOST RECENT generation
            if "session" not in last_item or "graph" not in last_item["session"]:
                return AgentResponse(success=False, error="Could not parse graph from the last queue item.")
                
            graph = last_item["session"]["graph"]
            
            # 2. Modify the graph dynamically
            import random
            new_seed = random.randint(0, 2147483647)
            
            prompt_injected = False
            
            for node_id, node in graph["nodes"].items():
                node_type = node.get("type", "")
                
                # Update text prompts
                if node_type == "string" and "positive" in node_id.lower():
                    node["value"] = prompt
                    prompt_injected = True
                elif node_type == "string" and "negative" in node_id.lower() and negative_prompt:
                    node["value"] = negative_prompt
                    
                # Update core metadata node
                elif node_type == "core_metadata":
                    node["positive_prompt"] = prompt
                    node["seed"] = new_seed
                    if steps:
                        node["steps"] = steps
                    if negative_prompt:
                        node["negative_prompt"] = negative_prompt
                        
                # Update seeds
                elif node_type == "integer" and "seed" in node_id.lower():
                    node["value"] = new_seed
                    
                # Update explicit denoise steps
                elif node_type in ("flux_denoise", "denoise_latents") and steps:
                    node["num_steps"] = steps
                    if "steps" in node:  # for older models
                        node["steps"] = steps
                        
            if not prompt_injected:
                 logger.warning("Could not clearly identify standard text prompt nodes. Proceeding anyway by updating core_metadata.")
                 
            # 3. Submit the new batch to InvokeAI
            batch_payload = {
                "batch": {
                    "graph": graph,
                    "runs": 1
                },
                "prepend": False
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{self._url}/api/v1/queue/default/enqueue_batch", json=batch_payload)
                if res.status_code in (200, 201):
                    new_item = res.json()
                    return AgentResponse(success=True, data={
                        "message": "Image generation queued successfully on InvokeAI!",
                        "prompt": prompt,
                        "batch_id": new_item.get("batch", {}).get("batch_id", "unknown"),
                        "seed": new_seed,
                        "status": "enqueued"
                    })
                else:
                    return AgentResponse(success=False, error=f"Enqueue failed: {res.status_code} - {res.text}")
                    
        except Exception as e:
            logger.error(f"Error invoking InvokeAI generation: {e}")
            return AgentResponse(success=False, error=str(e))
