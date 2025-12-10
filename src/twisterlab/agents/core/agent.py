"""
Minimal Agent core class to satisfy imports used by tests and rest of codebase.

This is a small compatibility shim intended solely to keep the test imports
and simple interactions working until a full implementation is restored.
"""

from __future__ import annotations

import uuid


class Agent:
    def __init__(self, name: str | None = None) -> None:
        self.name = name or "agent"
        self.agent_id = str(uuid.uuid4())

    async def run(self, context: dict) -> dict:
        """Simple run stub; may be overridden in tests."""
        return {
            "status": "ok",
            "agent_id": self.agent_id,
            "name": self.name,
            "ctx": context,
        }
