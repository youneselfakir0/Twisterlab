"""
Minimal OllamaClient stub used in tests and development when the real
implementation is unavailable.

This provides a small interface used by the LLM agent code and tests:
  - class OllamaClient
  - get_ollama_client()

Replace with the real client when available (Ollama gRPC/HTTP implementation).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class OllamaClient:
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or "http://localhost:11434"

    def generate(
        self, prompt: str, model: str = "llama3.2:1b", **kwargs
    ) -> Dict[str, Any]:
        # Return a simple mock response for tests
        return {
            "model": model,
            "prompt": prompt,
            "choices": [{"text": "<mocked response>", "index": 0}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }


def get_ollama_client(endpoint: Optional[str] = None) -> OllamaClient:
    return OllamaClient(endpoint)


__all__ = ["OllamaClient", "get_ollama_client"]
