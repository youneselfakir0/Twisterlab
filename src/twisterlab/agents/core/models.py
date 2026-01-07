"""
TwisterLab Database Models
SQLAlchemy ORM models for ticket tracking, agent logs, and system metrics
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TicketStatus(str, enum.Enum):
    """Ticket workflow states"""

    NEW = "new"
    CLASSIFIED = "classified"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    """Ticket priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Ticket(Base):
    """
    IT Support Ticket Model

    Stores user tickets with classification, resolution status, and agent responses.
    Used by ClassifierAgent and ResolverAgent for ticket workflow.
    """

    __tablename__ = "tickets"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    description: str = Column(Text, nullable=False)
    category: str = Column(
        String(100), nullable=True
    )  # Network, Software, Hardware, Account
    priority: TicketPriority = Column(
        SQLEnum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM
    )
    status: TicketStatus = Column(
        SQLEnum(TicketStatus), nullable=False, default=TicketStatus.NEW
    )
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    resolved_at: datetime = Column(DateTime(timezone=True), nullable=True)
    agent_response: dict = Column(
        JSON, nullable=True
    )  # Stores classifier/resolver output

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} category={self.category} priority={self.priority.value} status={self.status.value}>"


class AgentLog(Base):
    """
    Agent Execution Audit Log

    Tracks all agent executions for monitoring, debugging, and compliance.
    Includes execution time, result status, and error details.
    """

    __tablename__ = "agent_logs"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    agent_name: str = Column(String(100), nullable=False, index=True)
    ticket_id: int = Column(
        Integer, nullable=True, index=True
    )  # FK to tickets (not enforced for flexibility)
    action: str = Column(String(200), nullable=False)
    result: dict = Column(JSON, nullable=True)
    error: str = Column(Text, nullable=True)
    execution_time_ms: int = Column(
        Integer, nullable=True
    )  # Execution duration in milliseconds
    timestamp: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self) -> str:
        return f"<AgentLog id={self.id} agent={self.agent_name} action={self.action} timestamp={self.timestamp}>"


class SystemMetrics(Base):
    """
    System Health Metrics

    Stores system monitoring data from RealMonitoringAgent.
    Used for trend analysis, alerting, and capacity planning.
    """

    __tablename__ = "system_metrics"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    cpu_usage: float = Column(Float, nullable=False)
    memory_usage: float = Column(Float, nullable=False)
    disk_usage: float = Column(Float, nullable=False)
    docker_status: str = Column(
        String(50), nullable=True
    )  # healthy, degraded, unavailable
    timestamp: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self) -> str:
        return f"<SystemMetrics cpu={self.cpu_usage}% mem={self.memory_usage}% disk={self.disk_usage}% ts={self.timestamp}>"
