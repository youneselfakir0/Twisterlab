"""
TwisterLab Database Access Layer
Async PostgreSQL connection management using asyncpg driver
"""

import logging
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from twisterlab.agents.core.models import Base

logger = logging.getLogger(__name__)

# Database URL with asyncpg driver (required for async operations)


def _read_env_file(varname: str) -> str | None:
    """Read an environment variable from a file reference if present.

    Supports both VAR__FILE and VAR_FILE patterns to be compatible with
    different services (Grafana uses __FILE, Postgres env uses _FILE).
    Returns the file content without newline or None if not defined.
    """
    file_path = os.getenv(f"{varname}__FILE") or os.getenv(f"{varname}_FILE")
    if not file_path:
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not read env file for {varname}: {file_path}")
        return None


# Load DATABASE_URL from file if provided, else environment variable. Avoid
# embedding default plaintext passwords in source code; fall back to a
# connection string without a password where appropriate.
DATABASE_URL = (
    _read_env_file("DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or "postgresql+asyncpg://twisterlab@postgres:5432/twisterlab_prod"
)

# Override with specific components if provided
DB_USER = os.getenv("POSTGRES_USER", "twisterlab")
DB_PASSWORD = _read_env_file("POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "twisterlab_prod")

# Construct URL if individual components provided
if all([DB_USER, DB_HOST, DB_PORT, DB_NAME]):
    if DB_PASSWORD:
        DATABASE_URL = (
            "postgresql+asyncpg://"
            f"{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    else:
        DATABASE_URL = f"postgresql+asyncpg://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info(
    "Database URL configured: %s",
    (DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "localhost"),
)

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging (development only)
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Max concurrent connections
    max_overflow=20,  # Additional connections when pool exhausted
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_session() as session:
            # perform database operations
            pass
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in models.py if they don't exist.
    Safe to call multiple times (idempotent).
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def close_db() -> None:
    """
    Close database connection pool.

    Call this during application shutdown to gracefully close connections.
    """
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")


# FastAPI dependency for route handlers
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for injecting database sessions.

    Usage in route:
        @app.post("/tickets")
    async def create_ticket(session: AsyncSession):
            # session available here
            pass
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database transaction error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
