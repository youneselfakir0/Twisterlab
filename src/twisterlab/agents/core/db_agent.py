"""
Database Agent

MCP-agnostic agent for database operations.
Provides capabilities for querying and managing PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import List

from .base import (
    CoreAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


class DatabaseAgent(CoreAgent):
    """
    Agent for database operations.

    Provides capabilities for:
    - Executing SQL queries
    - Listing tables and schemas
    - Database health checks
    """

    @property
    def name(self) -> str:
        return "database"

    @property
    def description(self) -> str:
        return "PostgreSQL database operations and queries"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="execute_query",
                description="Execute a SQL query (SELECT only)",
                handler="handle_execute_query",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "sql",
                        ParamType.STRING,
                        "SQL query to execute (SELECT only)",
                    ),
                    CapabilityParam(
                        "limit",
                        ParamType.INTEGER,
                        "Maximum rows to return",
                        required=False,
                        default=100,
                    ),
                ],
                tags=["sql", "query"],
            ),
            AgentCapability(
                name="list_tables",
                description="List all tables in the database",
                handler="handle_list_tables",
                capability_type=CapabilityType.QUERY,
                tags=["schema", "tables"],
            ),
            AgentCapability(
                name="describe_table",
                description="Get schema for a specific table",
                handler="handle_describe_table",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "table_name",
                        ParamType.STRING,
                        "Name of the table to describe",
                    ),
                ],
                tags=["schema", "tables"],
            ),
            AgentCapability(
                name="db_health",
                description="Check database connection health",
                handler="handle_db_health",
                capability_type=CapabilityType.QUERY,
                tags=["health", "database"],
            ),
        ]

    # =========================================================================
    # Handler Methods
    # =========================================================================

    async def handle_execute_query(self, sql: str, limit: int = 100) -> AgentResponse:
        """Execute a SELECT query."""
        try:
            # Security: Only allow SELECT queries
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith("SELECT"):
                return AgentResponse(
                    success=False, error="Only SELECT queries are allowed for security"
                )

            # Add LIMIT if not present
            if "LIMIT" not in sql_upper:
                sql = f"{sql.rstrip(';')} LIMIT {limit}"

            db = self.registry.get_db()
            result = await db.query(sql)

            if result.error:
                return AgentResponse(success=False, error=result.error)

            return AgentResponse(
                success=True,
                data={
                    "columns": result.columns,
                    "rows": result.rows,
                    "row_count": result.row_count,
                },
            )
        except Exception as e:
            logger.exception("Query execution failed")
            return AgentResponse(success=False, error=str(e))

    async def handle_list_tables(self) -> AgentResponse:
        """List all tables."""
        try:
            db = self.registry.get_db()
            tables = await db.list_tables()

            return AgentResponse(
                success=True,
                data={
                    "tables": tables,
                    "count": len(tables),
                },
            )
        except Exception as e:
            logger.exception("Failed to list tables")
            return AgentResponse(success=False, error=str(e))

    async def handle_describe_table(self, table_name: str) -> AgentResponse:
        """Get table schema."""
        try:
            db = self.registry.get_db()
            schema = await db.get_table_schema(table_name)

            return AgentResponse(
                success=True,
                data={
                    "table": table_name,
                    "columns": schema,
                },
            )
        except Exception as e:
            logger.exception(f"Failed to describe table {table_name}")
            return AgentResponse(success=False, error=str(e))

    async def handle_db_health(self) -> AgentResponse:
        """Check database health."""
        try:
            db = self.registry.get_db()
            health = await db.health_check()

            return AgentResponse(
                success=True,
                data={
                    "status": health.status.value,
                    "latency_ms": health.latency_ms,
                    "message": health.message,
                    "metadata": health.metadata,
                },
            )
        except Exception as e:
            logger.exception("DB health check failed")
            return AgentResponse(success=False, error=str(e))
