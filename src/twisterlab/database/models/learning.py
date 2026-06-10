from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from twisterlab.database.session import Base

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_keywords: Mapped[str] = mapped_column(Text, nullable=True)  # comma-separated keywords
    steps: Mapped[dict] = mapped_column(JSON, nullable=False)  # list of execution steps
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)  # context, steps, outputs, status
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "*/5 * * * *" or human description parsed
    task_payload: Mapped[str] = mapped_column(Text, nullable=False)  # The task query
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default="default")
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
