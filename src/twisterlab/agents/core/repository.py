"""
TwisterLab Repository Layer
CRUD operations for database entities
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AgentLog, SystemMetrics, Ticket, TicketPriority, TicketStatus

logger = logging.getLogger(__name__)


class TicketRepository:
    """CRUD operations for IT support tickets"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        description: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        category: Optional[str] = None,
    ) -> Ticket:
        """Create a new ticket"""
        ticket = Ticket(
            description=description,
            priority=priority,
            category=category,
            status=TicketStatus.NEW,
        )
        self.session.add(ticket)
        await self.session.flush()  # Get ID without committing
        logger.info(
            f"Created ticket #{ticket.id}: {category or 'uncategorized'} ({priority.value})"
        )
        return ticket

    async def get(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket by ID"""
        result = await self.session.execute(
            select(Ticket).where(Ticket.id == ticket_id)
        )
        return result.scalars().first()

    async def list_all(self, limit: int = 100) -> List[Ticket]:
        """List all tickets (most recent first)"""
        result = await self.session.execute(
            select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_status(
        self, status: TicketStatus, limit: int = 100
    ) -> List[Ticket]:
        """List tickets by status"""
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.status == status)
            .order_by(Ticket.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_category(self, ticket_id: int, category: str) -> Optional[Ticket]:
        """Update ticket category (used by ClassifierAgent)"""
        ticket = await self.get(ticket_id)
        if ticket:
            ticket.category = category
            ticket.status = TicketStatus.CLASSIFIED
            ticket.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            logger.info(f"Ticket #{ticket_id} classified as: {category}")
        return ticket

    async def update_status(
        self,
        ticket_id: int,
        status: TicketStatus,
        agent_response: Optional[Dict[str, Any]] = None,
    ) -> Optional[Ticket]:
        """Update ticket status and optionally store agent response"""
        ticket = await self.get(ticket_id)
        if ticket:
            ticket.status = status
            ticket.updated_at = datetime.now(timezone.utc)

            if status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.now(timezone.utc)

            if agent_response:
                ticket.agent_response = agent_response

            await self.session.flush()
            logger.info(f"Ticket #{ticket_id} status updated: {status.value}")
        return ticket

    async def count_by_status(self) -> Dict[str, int]:
        """Get ticket counts by status"""
        result = await self.session.execute(
            select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
        )
        return {status.value: count for status, count in result.all()}


class AgentLogRepository:
    """CRUD operations for agent execution logs"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_execution(
        self,
        agent_name: str,
        action: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        ticket_id: Optional[int] = None,
        execution_time_ms: Optional[int] = None,
    ) -> AgentLog:
        """Log an agent execution"""
        log = AgentLog(
            agent_name=agent_name,
            action=action,
            result=result,
            error=error,
            ticket_id=ticket_id,
            execution_time_ms=execution_time_ms,
        )
        self.session.add(log)
        await self.session.flush()

        if error:
            logger.warning(f"Agent {agent_name} failed: {error}")
        else:
            logger.info(f"Agent {agent_name} executed: {action}")

        return log

    async def get_recent_logs(
        self, agent_name: Optional[str] = None, limit: int = 50
    ) -> List[AgentLog]:
        """Get recent agent logs, optionally filtered by agent name"""
        query = select(AgentLog).order_by(AgentLog.timestamp.desc()).limit(limit)

        if agent_name:
            query = query.where(AgentLog.agent_name == agent_name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_logs_for_ticket(self, ticket_id: int) -> List[AgentLog]:
        """Get all agent logs related to a specific ticket"""
        result = await self.session.execute(
            select(AgentLog)
            .where(AgentLog.ticket_id == ticket_id)
            .order_by(AgentLog.timestamp.asc())
        )
        return list(result.scalars().all())


class SystemMetricsRepository:
    """CRUD operations for system health metrics"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
        docker_status: str = "healthy",
    ) -> SystemMetrics:
        """Record system health metrics"""
        metrics = SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            docker_status=docker_status,
        )
        self.session.add(metrics)
        await self.session.flush()
        logger.debug(
            f"Recorded metrics: CPU={cpu_usage}%, MEM={memory_usage}%, DISK={disk_usage}%"
        )
        return metrics

    async def get_latest(self) -> Optional[SystemMetrics]:
        """Get most recent system metrics"""
        result = await self.session.execute(
            select(SystemMetrics).order_by(SystemMetrics.timestamp.desc()).limit(1)
        )
        return result.scalars().first()

    async def get_recent_metrics(self, limit: int = 100) -> List[SystemMetrics]:
        """Get recent system metrics for trend analysis"""
        result = await self.session.execute(
            select(SystemMetrics).order_by(SystemMetrics.timestamp.desc()).limit(limit)
        )
        return list(result.scalars().all())
