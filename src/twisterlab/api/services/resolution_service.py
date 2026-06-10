import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from twisterlab.api.schemas.common import UnifiedAgentResponse, AgentErrorCode
from twisterlab.api.services.agent_service import get_agent_service
from twisterlab.agents.core.repository import TicketRepository, AgentLogRepository

logger = logging.getLogger(__name__)

class ResolutionService:
    """
    Specialized service for ticket resolution and state management.
    Coordinates between Resolver Agent and long-term persistence.
    """

    def __init__(self):
        self.agent_service = get_agent_service()

    async def resolve_ticket(
        self, 
        category: str, 
        ticket_id: Optional[int] = None, 
        description: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> UnifiedAgentResponse:
        """
        Resolves a ticket by category and ID.
        Updates DB state if a session is provided.
        """
        logger.info(f"ResolutionService: Resolving ticket {ticket_id} (Category: {category})")
        
        try:
            # 1. Invoke Resolver Agent
            res = await self.agent_service.call_agent(
                "resolver", 
                "resolve_ticket", 
                ticket_id=str(ticket_id) if ticket_id else "unknown",
                resolution_note=description or "System auto-resolution"
            )
            
            if not res.success:
                logger.warning(f"ResolutionService: Resolver agent failed: {res.error}")
                return res

            # 2. Persist state if DB session is available
            if session and ticket_id:
                try:
                    ticket_repo = TicketRepository(session)
                    await ticket_repo.update_ticket_status(ticket_id, "resolved")
                    
                    # Log Execution for auditing
                    log_repo = AgentLogRepository(session)
                    await log_repo.log_execution(
                        agent_name="resolver",
                        action="resolve_ticket",
                        result=res.data,
                        ticket_id=ticket_id
                    )
                    res.metadata["db_updated"] = True
                except Exception as db_err:
                    logger.error(f"ResolutionService: Database update failed: {db_err}")
                    res.metadata["db_updated"] = False

            return res

        except Exception as e:
            logger.exception("ResolutionService: Unexpected failure during resolution")
            return UnifiedAgentResponse(
                success=False,
                error=str(e),
                error_code=AgentErrorCode.AGENT_FAILURE
            )

# Singleton provider
_resolution_service = None

def get_resolution_service() -> ResolutionService:
    global _resolution_service
    if _resolution_service is None:
        _resolution_service = ResolutionService()
    return _resolution_service
