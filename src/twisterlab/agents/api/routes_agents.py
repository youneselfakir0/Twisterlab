"""
Routes pour la gestion des agents via l'AgentRegistry
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from twisterlab.agents.registry import agent_registry

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/")
async def list_agents() -> Dict[str, Any]:
    """
    Liste tous les agents disponibles dans le registry
    """
    try:
        agents = agent_registry.list_agents()
        return {"status": "success", "agents": agents, "count": len(agents)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des agents: {str(e)}",
        )


@router.get("/{agent_name}")
async def get_agent(agent_name: str) -> Dict[str, Any]:
    """
    Récupère les informations d'un agent spécifique
    """
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_name}' non trouvé"
            )

        return {
            "status": "success",
            "agent": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "version": agent.version,
                "description": agent.description,
                "status": agent.status.value,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'agent: {str(e)}",
        )


@router.post("/{agent_name}/execute")
async def execute_agent(
    agent_name: str, payload: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Exécute un agent avec les paramètres fournis
    """
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_name}' non trouvé"
            )

        # Pour l'instant, on simule l'exécution
        # TODO: Implémenter l'exécution réelle des agents
        result = {
            "agent_name": agent.name,
            "status": "executed",
            "message": f"Agent {agent.name} exécuté avec succès",
            "payload": payload,
        }

        return {"status": "success", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de l'exécution de l'agent: {str(e)}"
        )


@router.get("/health")
async def agents_health() -> Dict[str, Any]:
    """
    Vérifie la santé du système de registry d'agents
    """
    try:
        agents = agent_registry.list_agents()
        healthy_count = len([a for a in agents.values() if a.get("status") == "active"])

        return {
            "status": "healthy" if healthy_count > 0 else "degraded",
            "total_agents": len(agents),
            "active_agents": healthy_count,
            "registry_status": "operational",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "registry_status": "failed"}
