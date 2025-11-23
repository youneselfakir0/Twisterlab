"""
TwisterLab Base Agent Module.

This module provides the foundation classes for all autonomous agents
in the TwisterLab system.
"""

from .base_agent import BaseAgent, accepts_context_or_task
from types import SimpleNamespace
import uuid


class TwisterAgent(BaseAgent):
    """Backward-compatible TwisterAgent wrapper.

    Historically TwisterAgent was the project's lightweight base class.
    In modern code BaseAgent provides the full behavior and abstract
    methods (including _process). Provide a simple wrapper that keeps
    the BaseAgent interface while implementing a default _process
    by delegating to the 'execute' API where available so legacy
    agents which only implement execute() can still be instantiated
    for tests and integration.
    """

    def __init__(
        self,
        name: str,
        display_name: str | None = None,
        description: str | None = None,
        role: str = "assistant",
        tools: list | None = None,
        model: str = "llama-3.2",
        temperature: float = 0.7,
        metadata: dict | None = None,
        instructions: str | None = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.display_name = display_name or name
        self.description = description or ""
        self.role = role
        self.instructions = instructions
        self.tools = tools or []
        self.model = model
        self.temperature = temperature
        self.metadata = metadata or {}

        # Stable unique agent identifier used across the registry and API
        self.agent_id = str(uuid.uuid4())

        # Compatibility: version used in UnifiedAgentBase; provide default
        self.version = "1.0"

        # Simple status object with a 'value' attribute (compat with unified AgentStatus)
        self.status = SimpleNamespace(value="READY")

    async def _process(self, context):
        # Delegate to execute. Many older agents implement execute() only.
        if hasattr(self, "execute"):
            try:
                return await self.execute(context.get("operation", "execute"), context)
            except TypeError:
                return await self.execute(context)
        raise NotImplementedError("_process() or execute() must be implemented by subclass")

    async def run(self, context: dict) -> dict:
        """Generic runner used by orchestrators to execute agent tasks.

        This is a minimal compatibility implementation that forwards to _process.
        """
        return await self._process(context)


__all__ = ["BaseAgent", "TwisterAgent", "accepts_context_or_task"]
