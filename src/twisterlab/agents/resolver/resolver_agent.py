"""
Minimal ResolverAgent shim to satisfy imports during testing.

This provides ResolutionStatus, ResolutionStrategy and a simple ResolverAgent
class used for unit and integration tests that do not rely on full resolver
implementation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ResolutionStatus(str, Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class ResolutionStrategy(str, Enum):
    DEFAULT = "DEFAULT"


class ResolverAgent:
    def __init__(self, name: str | None = None) -> None:
        self.name = name or "resolver"

    async def resolve(self, query: str) -> dict[str, Any]:
        return {"query": query, "result": "<mock>", "status": ResolutionStatus.RESOLVED}


__all__ = ["ResolverAgent", "ResolutionStrategy", "ResolutionStatus"]
