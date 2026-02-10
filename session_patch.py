from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Default to a shared in-memory SQLite database (safe for tests) unless overridden
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
if DATABASE_URL.startswith("postgres"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")

# Only create engine if DATABASE_URL is actually set (make it optional for MCP standalone)
if os.environ.get("DATABASE_URL"):
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # MCP standalone mode - no database
    engine = None
    AsyncSessionLocal = None


class Base(DeclarativeBase):
    pass
