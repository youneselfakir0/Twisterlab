import logging
import httpx
from typing import Optional, List, Dict, Any

# Centralized Settings (Sprint A - Operation Antigravity)
from twisterlab.config.unified_settings import settings

logger = logging.getLogger(__name__)

class CortexClient:
    """
    Client for Cortex AI services (Ollama/GPU).
    Uses DNS-based addressing for Phase 21 stability.
    """
    
    def __init__(self, endpoint: Optional[str] = None):
        self._endpoint = endpoint or settings.infra.ollama_base_url
        self._model = settings.infra.ollama_model
        logger.info(f"CortexClient initialized at {self._endpoint} (Model: {self._model})")

    @property
    def name(self) -> str:
        return "cortex"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call the AI generation endpoint."""
        url = f"{self._endpoint}/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096  # Limite de contexte pour éviter la saturation CPU
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get("response", "").strip()
            except Exception as e:
                logger.error(f"Cortex generation failed: {e}")
                return f"Error: AI node at {self._endpoint} unresponsive."

    async def get_available_models(self) -> List[str]:
        """Fetch models from the AI node."""
        url = f"{self._endpoint}/api/tags"
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    return [m.get("name") for m in data.get("models", [])]
            except Exception: pass
        return [self._model]
