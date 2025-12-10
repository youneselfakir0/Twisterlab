from __future__ import annotations

from typing import Dict, Any, Optional, List

try:
    from sqlalchemy.ext.asyncio import AsyncSession
except Exception:
    AsyncSession = object

from twisterlab.database.session import AsyncSessionLocal
from twisterlab.database import crud_agents


class DatabaseAgentRepo:
    """A small SQL-backed AgentRepo wrapper using the existing CRUD helpers.

    This implements the AgentRepo protocol so that API routes can swap in a DB
    backed repo easily for testing.
    """

    def __init__(self, session_maker=None) -> None:
        self._session_maker = session_maker or AsyncSessionLocal

    async def create_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        async with self._session_maker() as db:
            # crud.create_agent signature: (db, name, description)
            name = agent.get("name")
            description = agent.get("description")
            created = await crud_agents.create_agent(db, name, description)
            return {
                "id": str(created.id),
                "name": created.name,
                "description": created.description,
            }

    async def get_agent(
        self, agent_id: str, partition_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            aid = int(agent_id)
        except Exception:
            return None
        async with self._session_maker() as db:
            agent = await crud_agents.get_agent(db, aid)
            if not agent:
                return None
            return {
                "id": str(agent.id),
                "name": agent.name,
                "description": agent.description,
            }

    async def update_agent(
        self,
        agent_id: str,
        partition_key: Optional[str] = None,
        patch: Dict[str, Any] | None = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            aid = int(agent_id)
        except Exception:
            return None
        async with self._session_maker() as db:
            name = patch.get("name") if patch else None
            description = patch.get("description") if patch else None
            agent = await crud_agents.update_agent(
                db, aid, name=name, description=description
            )
            if not agent:
                return None
            return {
                "id": str(agent.id),
                "name": agent.name,
                "description": agent.description,
            }

    async def delete_agent(
        self, agent_id: str, partition_key: Optional[str] = None
    ) -> bool:
        try:
            aid = int(agent_id)
        except Exception:
            return False
        async with self._session_maker() as db:
            return await crud_agents.delete_agent(db, aid)

    async def list_agents(
        self, partition_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        async with self._session_maker() as db:
            agents = await crud_agents.get_agents(db)
            return [
                {"id": str(a.id), "name": a.name, "description": a.description}
                for a in agents
            ]


__all__ = ["DatabaseAgentRepo"]
