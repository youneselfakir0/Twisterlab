from __future__ import annotations
import logging
import contextlib
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase

# Centralized Settings (Sprint A)
from twisterlab.config.unified_settings import settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Unified Declarative Base for TwisterLab v4.0."""
    pass

class DatabaseManager:
    """
    Thread-safe Async Singleton managing SQLAlchemy Engine and Session Pool.
    Implements Operation Antigravity Data Layer standards.
    """
    _instance: Optional[DatabaseManager] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._engine = None
            cls._instance._sessionmaker = None
        return cls._instance

    def init(self):
        """Lazy initialization of the engine and pool."""
        if self._engine is not None:
            return

        db_url = settings.infra.database_url
        logger.info(f"DatabaseManager: Initializing pool for {settings.infra.postgres_host}")
        
        self._engine = create_async_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=20,
            max_overflow=10,
            echo=settings.core.debug
        )
        
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    async def close(self):
        """Graceful shutdown of the engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for safe session handling."""
        if self._sessionmaker is None:
            self.init()
            
        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncGenerator[AsyncConnection, None]:
        """Context manager for direct connection handling (e.g. for migrations)."""
        if self._engine is None:
            self.init()
        async with self._engine.begin() as conn:
            yield conn

    async def check_health(self) -> bool:
        """Verify database connectivity."""
        try:
            async with self.session() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global instance
db_manager = DatabaseManager()
