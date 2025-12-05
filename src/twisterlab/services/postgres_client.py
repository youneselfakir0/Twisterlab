"""
PostgreSQL Database Client

Concrete implementation of DBClient for PostgreSQL.
Connects to EdgeServer PostgreSQL at 192.168.0.30:5432.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional
from urllib.parse import urlparse

from .base import (
    DBClient,
    QueryResult,
    ServiceHealth,
    ServiceStatus,
)

logger = logging.getLogger(__name__)

# Try to import asyncpg
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logger.warning("asyncpg not available - DB client will use fallback mode")


class PostgresClient(DBClient):
    """
    Database client for PostgreSQL.
    
    Provides async access to PostgreSQL with connection pooling.
    """
    
    def __init__(
        self,
        url: str = "postgresql://postgres:postgres@192.168.0.30:5432/twisterlab",
    ):
        """
        Initialize PostgreSQL client.
        
        Args:
            url: PostgreSQL connection URL in format:
                 postgresql://user:password@host:port/database
        """
        self._url = url
        
        # Parse URL
        parsed = urlparse(url.replace("postgresql://", "postgres://"))
        self._host = parsed.hostname or "192.168.0.30"
        self._port = parsed.port or 5432
        self._database = (parsed.path or "/twisterlab").lstrip("/")
        self._user = parsed.username or "postgres"
        self._password = parsed.password or os.getenv("POSTGRES_PASSWORD", "")
        
        self._pool: Optional["asyncpg.Pool"] = None
        logger.info(f"PostgresClient initialized: {self._host}:{self._port}/{self._database}")
    
    @property
    def name(self) -> str:
        return "postgresql"
    
    async def _get_pool(self) -> "asyncpg.Pool":
        """Get or create connection pool."""
        if self._pool is None:
            if not ASYNCPG_AVAILABLE:
                raise RuntimeError("asyncpg not available")
            self._pool = await asyncpg.create_pool(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._user,
                password=self._password,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
        return self._pool
    
    async def query(
        self,
        sql: str,
        params: Optional[List[Any]] = None
    ) -> QueryResult:
        """Execute a SELECT query and return results."""
        if not ASYNCPG_AVAILABLE:
            return QueryResult(rows=[], columns=[], row_count=0)
        
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                # Use fetch for SELECT queries
                if params:
                    rows = await conn.fetch(sql, *params)
                else:
                    rows = await conn.fetch(sql)
                
                if rows:
                    columns = list(rows[0].keys())
                    data = [dict(row) for row in rows]
                    return QueryResult(
                        rows=data,
                        columns=columns,
                        row_count=len(data)
                    )
                return QueryResult(rows=[], columns=[], row_count=0)
                
        except Exception as e:
            logger.error(f"PostgreSQL query error: {e}")
            return QueryResult(rows=[], columns=[], row_count=0, error=str(e))
    
    async def execute(
        self,
        sql: str,
        params: Optional[List[Any]] = None
    ) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows."""
        if not ASYNCPG_AVAILABLE:
            return 0
        
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                if params:
                    result = await conn.execute(sql, *params)
                else:
                    result = await conn.execute(sql)
                
                # Parse "INSERT 0 1" style result
                parts = result.split()
                if len(parts) >= 2 and parts[-1].isdigit():
                    return int(parts[-1])
                return 0
                
        except Exception as e:
            logger.error(f"PostgreSQL execute error: {e}")
            return 0
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator:
        """Context manager for transactions."""
        if not ASYNCPG_AVAILABLE:
            yield None
            return
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def list_tables(self) -> List[str]:
        """List all tables in the database."""
        result = await self.query("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        return [row["tablename"] for row in result.rows]
    
    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema for a specific table."""
        result = await self.query(
            """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = 'public'
            ORDER BY ordinal_position
            """,
            [table_name]
        )
        return result.rows
    
    async def health_check(self) -> ServiceHealth:
        """Check PostgreSQL health."""
        if not ASYNCPG_AVAILABLE:
            return ServiceHealth(
                name=self.name,
                status=ServiceStatus.DEGRADED,
                message="asyncpg library not available"
            )
        
        try:
            start = time.perf_counter()
            pool = await self._get_pool()
            
            async with pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                elapsed = (time.perf_counter() - start) * 1000
                
                return ServiceHealth(
                    name=self.name,
                    status=ServiceStatus.CONNECTED,
                    latency_ms=elapsed,
                    message="OK",
                    metadata={
                        "version": version.split(",")[0] if version else None,
                        "database": self._database,
                        "pool_size": pool.get_size(),
                    }
                )
                
        except Exception as e:
            return ServiceHealth(
                name=self.name,
                status=ServiceStatus.DISCONNECTED,
                message=str(e)
            )
    
    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
