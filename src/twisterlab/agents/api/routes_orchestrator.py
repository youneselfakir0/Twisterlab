"""
Routes pour l'orchestrateur d'agents
"""

from fastapi import APIRouter

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.get("/health")
async def orchestrator_health():
    """
    Point de terminaison de santé pour l'orchestrateur
    """
    return {
        "status": "healthy",
        "service": "orchestrator",
        "message": "Orchestrator service is operational",
    }


@router.post("/workflows")
async def create_workflow():
    """
    Crée un nouveau workflow d'agents
    """
    return {
        "status": "success",
        "message": "Workflow creation not yet implemented",
        "workflow_id": None,
    }
