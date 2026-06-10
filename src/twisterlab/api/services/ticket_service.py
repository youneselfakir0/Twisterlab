"""
Ticket Service Layer
Encapsulates business logic for ticket classification and resolution.
Coordinates between database repositories and agent executions.
"""

import logging
import time
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from twisterlab.api.schemas.common import UnifiedAgentResponse, AgentErrorCode, TicketCategory, TicketPriority
from twisterlab.api.services.agent_service import get_agent_service
from twisterlab.agents.core.repository import TicketRepository, AgentLogRepository
from twisterlab.agents.core.models import TicketPriority as DBTicketPriority

logger = logging.getLogger(__name__)

class TicketService:
    """
    Handles the high-level workflow for support tickets.
    Orchestrates classification, resolution, and database persistence.
    """

    def __init__(self):
        self.agent_service = get_agent_service()

    async def classify_ticket(
        self, 
        description: str, 
        priority_override: Optional[str] = None, 
        session: Optional[AsyncSession] = None
    ) -> UnifiedAgentResponse:
        """
        Executes the ticket classification workflow.
        1. Calls the Classifier Agent.
        2. Persists the ticket to the database (if session provided).
        3. Logs the execution.
        """
        try:
            # 1. Invoke Agent via Service Facade
            logger.info(f"TicketService: Requesting classification for '{description[:50]}...'")
            agent_res = await self.agent_service.call_agent(
                "classifier", 
                "classify_ticket", 
                ticket_text=description
            )
            
            if not agent_res.success:
                return agent_res

            # 2. Extract results
            result_data = agent_res.data
            category = result_data.get("category")
            priority = priority_override or result_data.get("priority", "medium")
            
            # 3. Database Persistence (Optional/Graceful Fallback)
            ticket_id = None
            if session:
                try:
                    ticket_repo = TicketRepository(session)
                    # Map override priority
                    db_priority = DBTicketPriority(priority) if priority in [p.value for p in DBTicketPriority] else DBTicketPriority.MEDIUM
                    
                    ticket = await ticket_repo.create_ticket(
                        description=description,
                        category=category,
                        priority=db_priority
                    )
                    ticket_id = ticket.id
                    result_data["ticket_id"] = ticket_id
                    
                    # Log Agent Execution
                    log_repo = AgentLogRepository(session)
                    await log_repo.log_execution(
                        agent_name="classifier",
                        action="classify_ticket",
                        result=result_data,
                        ticket_id=ticket_id
                    )
                except Exception as db_err:
                    logger.warning(f"TicketService: DB execution failed, continuing in fallback mode: {db_err}")

            return UnifiedAgentResponse(
                success=True,
                data=result_data,
                metadata={"ticket_id": ticket_id, "db_sync": session is not None}
            )

        except Exception as e:
            logger.exception("TicketService: Classification failed")
            return UnifiedAgentResponse(
                success=False,
                error=str(e),
                error_code=AgentErrorCode.AGENT_FAILURE
            )

    async def resolve_ticket(
        self,
        category: str,
        ticket_id: Optional[int] = None,
        description: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> UnifiedAgentResponse:
        """
        Executes the ticket resolution workflow.
        """
        try:
            # 1. Invoke Resolver Agent
            logger.info(f"TicketService: Requesting resolution for category '{category}'")
            agent_res = await self.agent_service.call_agent(
                "resolver",
                "resolve_ticket",
                ticket_id=str(ticket_id) if ticket_id else "unknown",
                resolution_note=description or "Automatic resolution requested"
            )
            
            if not agent_res.success:
                return agent_res

            # 2. Update Database (if session provided)
            if session and ticket_id:
                try:
                    ticket_repo = TicketRepository(session)
                    await ticket_repo.update_ticket_status(ticket_id, "resolved")
                    
                    # Log Execution
                    log_repo = AgentLogRepository(session)
                    await log_repo.log_execution(
                        agent_name="resolver",
                        action="resolve_ticket",
                        result=agent_res.data,
                        ticket_id=ticket_id
                    )
                except Exception as db_err:
                    logger.warning(f"TicketService: DB update failed: {db_err}")

            return agent_res

        except Exception as e:
            logger.exception("TicketService: Resolution failed")
            return UnifiedAgentResponse(
                success=False,
                error=str(e),
                error_code=AgentErrorCode.AGENT_FAILURE
            )

# Global Service Singleton
_ticket_service = None

def get_ticket_service() -> TicketService:
    global _ticket_service
    if _ticket_service is None:
        _ticket_service = TicketService()
    return _ticket_service
