"""
Cortex/Ollama LLM Client

Concrete implementation of LLMClient for Ollama-compatible endpoints.
Supports Cortex server at 192.168.0.20:11434.
"""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from .base import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    ServiceHealth,
    ServiceStatus,
)

logger = logging.getLogger(__name__)

# Try to import httpx for async HTTP
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available - LLM client will use fallback mode")


class CortexClient(LLMClient):
    """
    LLM client for Cortex/Ollama server.

    Connects to Ollama-compatible API at the configured endpoint.
    Supports: llama3.2, qwen3, deepseek-r1, and other Ollama models.
    """

    def __init__(self, endpoint: str = "http://192.168.0.20:11434"):
        self._endpoint = endpoint.rstrip("/")
        self._default_model = "llama3.2:1b"
        self._timeout = 60.0
        logger.info(f"CortexClient initialized: {self._endpoint}")

    @property
    def name(self) -> str:
        return "cortex-ollama"

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using Ollama generate API."""
        if not HTTPX_AVAILABLE:
            return self._fallback_response(prompt, model)

        model = model or self._default_model
        url = f"{self._endpoint}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                start = time.perf_counter()
                response = await client.post(url, json=payload)
                response.raise_for_status()
                elapsed = time.perf_counter() - start

                data = response.json()

                return LLMResponse(
                    text=data.get("response", ""),
                    model=model,
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    total_tokens=data.get("prompt_eval_count", 0)
                    + data.get("eval_count", 0),
                    finish_reason="stop",
                    metadata={
                        "elapsed_ms": elapsed * 1000,
                        "eval_duration": data.get("eval_duration"),
                    },
                )
        except Exception as e:
            logger.error(f"LLM generate error: {e}")
            return LLMResponse(
                text=f"Error: {str(e)}",
                model=model,
                finish_reason="error",
                metadata={"error": str(e)},
            )

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        """Chat completion using Ollama chat API."""
        if not HTTPX_AVAILABLE:
            prompt = messages[-1].content if messages else ""
            return self._fallback_response(prompt, model)

        model = model or self._default_model
        url = f"{self._endpoint}/api/chat"

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                start = time.perf_counter()
                response = await client.post(url, json=payload)
                response.raise_for_status()
                elapsed = time.perf_counter() - start

                data = response.json()
                message = data.get("message", {})

                return LLMResponse(
                    text=message.get("content", ""),
                    model=model,
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    total_tokens=data.get("prompt_eval_count", 0)
                    + data.get("eval_count", 0),
                    finish_reason="stop",
                    metadata={
                        "elapsed_ms": elapsed * 1000,
                        "role": message.get("role"),
                    },
                )
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return LLMResponse(
                text=f"Error: {str(e)}",
                model=model,
                finish_reason="error",
                metadata={"error": str(e)},
            )

    async def stream(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        if not HTTPX_AVAILABLE:
            yield "[Streaming not available - httpx not installed]"
            return

        model = model or self._default_model
        url = f"{self._endpoint}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line:
                            import json

                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield f"[Error: {str(e)}]"

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from Ollama."""
        if not HTTPX_AVAILABLE:
            return [{"name": self._default_model, "status": "fallback"}]

        url = f"{self._endpoint}/api/tags"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("models", [])
        except Exception as e:
            logger.error(f"List models error: {e}")
            return []

    async def health_check(self) -> ServiceHealth:
        """Check Ollama server health."""
        if not HTTPX_AVAILABLE:
            return ServiceHealth(
                name=self.name,
                status=ServiceStatus.DEGRADED,
                message="httpx not available",
            )

        try:
            start = time.perf_counter()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._endpoint}/api/tags")
                elapsed = (time.perf_counter() - start) * 1000

                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get("models", []))
                    return ServiceHealth(
                        name=self.name,
                        status=ServiceStatus.CONNECTED,
                        latency_ms=elapsed,
                        message=f"{model_count} models available",
                        metadata={"endpoint": self._endpoint, "models": model_count},
                    )
                else:
                    return ServiceHealth(
                        name=self.name,
                        status=ServiceStatus.DEGRADED,
                        latency_ms=elapsed,
                        message=f"HTTP {response.status_code}",
                    )
        except Exception as e:
            return ServiceHealth(
                name=self.name, status=ServiceStatus.DISCONNECTED, message=str(e)
            )

    def _fallback_response(self, prompt: str, model: Optional[str]) -> LLMResponse:
        """Fallback response when httpx is not available."""
        return LLMResponse(
            text="[LLM unavailable - httpx not installed]",
            model=model or self._default_model,
            finish_reason="error",
            metadata={"fallback": True},
        )
