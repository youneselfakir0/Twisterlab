"""
Routes MCP (Model Context Protocol) pour l'intégration avec les IDE
"""

from fastapi import APIRouter

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/health")
async def mcp_health():
    """
    Point de terminaison de santé pour MCP
    """
    return {
        "status": "healthy",
        "service": "mcp",
        "message": "MCP service is operational",
    }


@router.post("/tools")
async def list_tools():
    """
    Liste les outils disponibles via MCP
    """
    return {
        "status": "success",
        "tools": [
            {
                "name": "agent_registry",
                "description": "Accès au registre des agents TwisterLab",
                "version": "1.0.0",
            }
        ],
    }
