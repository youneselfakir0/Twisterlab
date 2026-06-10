from __future__ import annotations

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# Default to a local SQLite database
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///twisterlab.db")
if DATABASE_URL.startswith("postgres"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")

# STABILIZED ENGINE with pool_pre_ping and connection recycling
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


async def init_db():
    async with engine.begin() as conn:
        try:
            from twisterlab.database.models import agent as _agent_model  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            logger.error(f"Failed to initialize agent models: {e}")
            
        try:
            from twisterlab.database.models import resilience as _resilience_model  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            logger.error(f"Failed to initialize resilience models: {e}")
