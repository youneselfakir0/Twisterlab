from __future__ import annotations
import logging
import json
from typing import List, Dict, Any, Optional

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)
from twisterlab.agents.real.n8n_navigator_agent import N8nNavigatorAgent

logger = logging.getLogger(__name__)

class RealStockManagerAgent(TwisterAgent):
    """Agent de gestion des stocks et de l'inventaire via n8n."""

    def __init__(self, registry=None) -> None:
        super().__init__(registry)
        self._n8n = N8nNavigatorAgent(registry)

    @property
    def name(self) -> str:
        return "real-stock-manager"

    @property
    def description(self) -> str:
        return "Gère l'inventaire et les niveaux de stock via des workflows n8n connectés à l'ERP/CRM"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="check_inventory",
                description="Vérifie le niveau de stock d'un produit spécifique",
                handler="handle_check_inventory",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("product_name", ParamType.STRING, "Nom ou ID du produit", required=True),
                    CapabilityParam("warehouse", ParamType.STRING, "Entrepôt spécifique (optionnel)", required=False),
                ],
            ),
            AgentCapability(
                name="update_stock",
                description="Met à jour manuellement le niveau de stock (ex: inventaire physique)",
                handler="handle_update_stock",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("product_name", ParamType.STRING, "Nom ou ID du produit", required=True),
                    CapabilityParam("quantity", ParamType.INTEGER, "Nouvelle quantité en stock", required=True),
                    CapabilityParam("reason", ParamType.STRING, "Raison du changement", required=False, default="manual update"),
                ],
            ),
        ]

    async def handle_check_inventory(self, product_name: str, warehouse: Optional[str] = None) -> AgentResponse:
        payload = {"product": product_name, "warehouse": warehouse, "action": "check"}
        return await self._n8n.handle_trigger_webhook("inventory-management", payload=json.dumps(payload))

    async def handle_update_stock(self, product_name: str, quantity: int, reason: str = "manual update") -> AgentResponse:
        payload = {"product": product_name, "quantity": quantity, "reason": reason, "action": "update"}
        return await self._n8n.handle_trigger_webhook("inventory-management", payload=json.dumps(payload))

__all__ = ["RealStockManagerAgent"]
