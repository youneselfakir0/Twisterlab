"""
TwisterLab Resilience Database Models
v5.1.0: Persistence Layer for Circuit Breakers and Self-Healing Metrics
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Float, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..session import Base

class CapabilityMetric(Base):
    """Tracks historical success rate for adaptive retry limits."""
    __tablename__ = "capabilities_metrics"

    capability_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    current_success_rate: Mapped[float] = mapped_column(Float, default=100.0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CircuitBreaker(Base):
    """Tracks state and exponential backoff quarantine for capability circuit breakers."""
    __tablename__ = "circuit_breakers"

    capability_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="active") # active, quarantined
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    quarantine_count: Mapped[int] = mapped_column(Integer, default=0)
    quarantined_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class HealingLog(Base):
    """Audits each self-healing event, protecting against duplicates using a unique idempotency request_id."""
    __tablename__ = "healing_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    capability_name: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str] = mapped_column(String(50)) # sql, cache, llm, network
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
