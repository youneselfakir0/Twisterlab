"""
Base Agent module for TwisterLab.

Provides the foundational BaseAgent class and utilities.
"""

from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Any, Dict
import uuid


def accepts_context_or_task(func):
    """Decorator for backward compatibility with different execute signatures."""
    return func


class BaseAgent(ABC):
    """Abstract base class for all TwisterLab agents."""

    def __init__(self):
        self.agent_id = str(uuid.uuid4())
        self.status = SimpleNamespace(value="READY")
        self.version = "1.0"

    @abstractmethod
    async def _process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task context. Must be implemented by subclasses."""
        pass

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with the given context."""
        return await self._process(context)


__all__ = ["BaseAgent", "accepts_context_or_task"]
