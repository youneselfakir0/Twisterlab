"""TwisterLab Base Agent Module."""

from .base_agent import BaseAgent, accepts_context_or_task
from datetime import datetime, timezone


class TwisterAgent(BaseAgent):
    """Full-featured TwisterAgent with multi-framework support."""

    def __init__(
        self,
        name: str,
        display_name: str = None,
        description: str = None,
        role: str = "assistant",
        tools: list = None,
        model: str = "llama-3.2",
        temperature: float = 0.7,
        metadata: dict = None,
        instructions: str = None,
    ):
        super().__init__()
        self.name = name
        self.display_name = display_name or name
        self.description = description or ""
        self.role = role
        self.tools = tools or []
        self.model = model
        self.temperature = temperature
        self.metadata = metadata or {}
        self.instructions = (
            instructions or f"You are {self.display_name}, {self.description}"
        )
        self.created_at = datetime.now(timezone.utc).isoformat() + "Z"

    async def _process(self, context):
        if hasattr(self, "execute"):
            return await self.execute(context.get("task", ""), context)
        raise NotImplementedError()

    async def execute(self, task, context=None):
        return {"status": "not_implemented", "task": task}


__all__ = ["BaseAgent", "TwisterAgent", "accepts_context_or_task"]
