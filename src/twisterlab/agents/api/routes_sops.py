"""
Routes pour les procédures opérationnelles standard (SOPs)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/sops", tags=["sops"])


@router.get("/health")
async def sops_health():
    """
    Point de terminaison de santé pour les SOPs
    """
    return {
        "status": "healthy",
        "service": "sops",
        "message": "SOPs service is operational",
    }


@router.get("/")
async def list_sops():
    """
    Liste toutes les procédures opérationnelles standard
    """
    return {
        "status": "success",
        "sops": [],
        "message": "SOPs listing not yet implemented",
    }
