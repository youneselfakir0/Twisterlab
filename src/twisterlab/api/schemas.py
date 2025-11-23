from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

# --- Schémas pour les Payloads des Requêtes ---


class AgentExecutePayload(BaseModel):
    """
    Schéma de validation pour le payload de l'endpoint d'exécution d'agent.
    Garantit que les requêtes contiennent les champs nécessaires.
    """

    operation: str = Field(
        ...,
        description="The specific operation the agent should perform (e.g., 'classify_ticket', 'resolve_ticket').",
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="A flexible dictionary containing all necessary context for the operation.",
    )

    class Config:
        extra = "allow"  # Permet des champs supplémentaires dans le context
        schema_extra = {
            "example": {
                "operation": "classify_ticket",
                "context": {
                    "ticket_id": "T-123",
                    "title": "Cannot connect to WiFi",
                    "description": "My laptop is not connecting to the office WiFi network.",
                },
            }
        }


# --- Schémas pour les Réponses ---


class HealthResponse(BaseModel):
    """Schéma de réponse pour l'endpoint de santé."""

    status: str
    version: str
    timestamp: str


class AgentMetadata(BaseModel):
    """Schéma pour les métadonnées d'un agent."""

    agent_id: str
    name: str
    version: str
    description: str
    status: str


class AgentListResponse(BaseModel):
    """Schéma de réponse pour la liste des agents."""

    agents: list[AgentMetadata]
    total: int


class AgentExecutionResult(BaseModel):
    """Schéma générique pour le résultat d'une exécution d'agent."""

    status: str
    message: Optional[str] = None
    # ... d'autres champs peuvent être ajoutés ici selon les retours des agents


class AgentExecutionResponse(BaseModel):
    """Schéma de réponse pour l'endpoint d'exécution d'agent."""

    agent_name: str
    agent_id: str
    status: str
    timestamp: str
    result: Dict[str, Any]  # Le résultat peut être complexe et varié
