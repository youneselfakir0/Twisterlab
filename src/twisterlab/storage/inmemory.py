from __future__ import annotations

from typing import Dict, List, Optional, Any
from uuid import uuid4


class InMemoryAgentRepo:
    """A small in-memory agent repository used by tests and the simple dev server.

    Not intended for production use - this gives an implementation of the
    AgentRepo Protocol for the API dependency injection.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, Dict[str, Any]] = {}

    async def create_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = str(uuid4())
        agent_obj = {"id": agent_id, **agent}
        self._agents[agent_id] = agent_obj
        return agent_obj

    async def get_agent(
        self, agent_id: str, partition_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        return self._agents.get(agent_id)

    async def update_agent(
        self,
        agent_id: str,
        partition_key: Optional[str] = None,
        patch: Dict[str, Any] | None = None,
    ) -> Optional[Dict[str, Any]]:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        if patch:
            agent.update(patch)
        self._agents[agent_id] = agent
        return agent

    async def delete_agent(
        self, agent_id: str, partition_key: Optional[str] = None
    ) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    async def list_agents(
        self, partition_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return list(self._agents.values())


__all__ = ["InMemoryAgentRepo"]
