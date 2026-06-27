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

class RealOrderProcessorAgent(TwisterAgent):
    """Agent de traitement des commandes client via n8n."""

    def __init__(self, registry=None) -> None:
        super().__init__(registry)
        self._n8n = N8nNavigatorAgent(registry)

    @property
    def name(self) -> str:
        return "real-order-processor"

    @property
    def description(self) -> str:
        return "Gère le cycle de vie des commandes (création, suivi, annulation) via n8n"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="create_order",
                description="Crée une nouvelle commande client",
                handler="handle_create_order",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("customer_id", ParamType.STRING, "ID du client", required=True),
                    CapabilityParam("items", ParamType.ARRAY, "Liste des produits et quantités", required=True),
                    CapabilityParam("shipping_address", ParamType.STRING, "Adresse de livraison", required=False),
                ],
            ),
            AgentCapability(
                name="track_order",
                description="Récupère le statut actuel d'une commande",
                handler="handle_track_order",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("order_id", ParamType.STRING, "ID de la commande", required=True),
                ],
            ),
        ]

    async def handle_create_order(self, customer_id: str, items: List[Dict[str, Any]], shipping_address: Optional[str] = None) -> AgentResponse:
        payload = {"customer_id": customer_id, "items": items, "shipping_address": shipping_address, "action": "create"}
        return await self._n8n.handle_trigger_webhook("order-processing", payload=json.dumps(payload))

    async def handle_track_order(self, order_id: str) -> AgentResponse:
        payload = {"order_id": order_id, "action": "track"}
        return await self._n8n.handle_trigger_webhook("order-processing", payload=json.dumps(payload))

__all__ = ["RealOrderProcessorAgent"]
