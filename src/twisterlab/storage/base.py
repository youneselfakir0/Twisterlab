from __future__ import annotations

from typing import Protocol, Optional, List, Dict, Any


class AgentRepo(Protocol):
    """Protocol that describes the minimal Agent repository used by the API routes.

    This is intentionally small - it is implemented by an in-memory test repo for
    unit/integration tests and may be swapped to a real DB-backed implementation
    when available.
    """

    async def create_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]: ...

    async def get_agent(
        self, agent_id: str, partition_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]: ...

    async def update_agent(
        self,
        agent_id: str,
        partition_key: Optional[str] = None,
        patch: Dict[str, Any] | None = None,
    ) -> Optional[Dict[str, Any]]: ...

    async def delete_agent(
        self, agent_id: str, partition_key: Optional[str] = None
    ) -> bool: ...

    async def list_agents(
        self, partition_key: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...


__all__ = ["AgentRepo"]
