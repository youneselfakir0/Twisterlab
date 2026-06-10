import logging
from typing import Optional, Dict, Any
from twisterlab.api.schemas.common import UnifiedAgentResponse, AgentErrorCode
from twisterlab.api.services.agent_service import get_agent_service

logger = logging.getLogger(__name__)

class ClassificationService:
    """
    Specialized service for ticket and text classification.
    Wraps the Classifier Agent and ensures normalized outputs.
    """

    def __init__(self):
        self.agent_service = get_agent_service()

    async def classify_ticket(self, description: str) -> UnifiedAgentResponse:
        """
        Classifies a ticket description into category and priority.
        """
        logger.info(f"ClassificationService: Analyzing ticket: '{description[:50]}...'")
        
        try:
            # Call agent via unified service
            res = await self.agent_service.call_agent(
                "classifier", 
                "classify_ticket", 
                ticket_text=description
            )
            
            if not res.success:
                logger.warning(f"ClassificationService: Agent call failed: {res.error}")
                return res

            # Ensure data contains expected keys
            data = res.data or {}
            if "category" not in data:
                data["category"] = "general"
            if "priority" not in data:
                data["priority"] = "medium"

            return UnifiedAgentResponse(
                success=True,
                data=data,
                metadata=res.metadata
            )

        except Exception as e:
            logger.exception("ClassificationService: Unexpected failure during classification")
            return UnifiedAgentResponse(
                success=False,
                error=str(e),
                error_code=AgentErrorCode.AGENT_FAILURE
            )

# Singleton provider
_classification_service = None

def get_classification_service() -> ClassificationService:
    global _classification_service
    if _classification_service is None:
        _classification_service = ClassificationService()
    return _classification_service
