"""
TwisterLab MCP API Routes - Real Agent Endpoints
Production-ready FastAPI routes for MCP tool integration
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

# Import database layer

# Import real agents
from twisterlab.agents.core.database import get_db_session
from twisterlab.agents.core.models import TicketPriority
from twisterlab.agents.core.repository import (
    AgentLogRepository,
    TicketRepository,
)
from twisterlab.agents.real.real_backup_agent import RealBackupAgent
from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
from twisterlab.agents.real.real_desktop_commander_agent import (
    RealDesktopCommanderAgent,
)
from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
from twisterlab.agents.real.real_resolver_agent import RealResolverAgent
from twisterlab.agents.real.real_sentiment_analyzer_agent import (
    SentimentAnalyzerAgent,
)
from twisterlab.agents.real.real_sync_agent import RealSyncAgent
from twisterlab.agents.real.browser_agent import RealBrowserAgent
from twisterlab.agents.real.real_code_review_agent import RealCodeReviewAgent

# Configure logging
logger = logging.getLogger(__name__)

# Create router (prefix is defined in api/main.py, not here)
router = APIRouter(tags=["mcp-tools"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class MCPResponse(BaseModel):
    """Standard MCP response format."""

    status: str = Field(..., pattern="^(ok|error)$")
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ============================================================================
# REGISTRY ENDPOINT - List All Agents
# ============================================================================


@router.post("/list_autonomous_agents", response_model=MCPResponse)
@router.get("/list_autonomous_agents", response_model=MCPResponse)
async def list_autonomous_agents() -> MCPResponse:
    """
    List all 8 real autonomous agents with metadata.

    Returns:
        MCPResponse with agent registry data
    """
    try:
        agents_data = {
            "version": "2.1.0",
            "total": 9,
            "base_class": "twisterlab.agents.base.TwisterAgent",
            "agents": [
                {
                    "name": "RealBrowserAgent",
                    "module": "twisterlab.agents.real.browser_agent",
                    "file": "src/twisterlab/agents/real/browser_agent.py",
                    "mcp_tool": "browse_web",
                    "description": "Real web browsing and scraping using Playwright",
                    "capabilities": ["browse", "screenshot", "scrape"],
                    "status": "operational",
                },
                {
                    "name": "RealCodeReviewAgent",
                    "module": "twisterlab.agents.real.real_code_review_agent",
                    "mcp_tool": "analyze_code",
                    "description": "Analyze code for issues and security vulnerabilities",
                    "capabilities": ["analyze_code", "security_scan"],
                    "status": "operational",
                },
                {
                    "name": "RealMonitoringAgent",
                    "module": "twisterlab.agents.real.real_monitoring_agent",
                    "file": "src/twisterlab/agents/real/real_monitoring_agent.py",
                    "mcp_tool": "monitor_system_health",
                    "description": "System health monitoring (CPU, RAM, disk, Docker services)",
                    "capabilities": [
                        "cpu_monitoring",
                        "ram_monitoring",
                        "disk_monitoring",
                        "docker_health",
                    ],
                    "status": "operational",
                },
                {
                    "name": "RealBackupAgent",
                    "module": "twisterlab.agents.real.real_backup_agent",
                    "file": "src/twisterlab/agents/real/real_backup_agent.py",
                    "mcp_tool": "create_backup",
                    "description": "Automated backups with disaster recovery (PostgreSQL, Redis, configs)",
                    "capabilities": [
                        "postgres_backup",
                        "redis_backup",
                        "config_backup",
                        "incremental_backup",
                    ],
                    "status": "operational",
                },
                {
                    "name": "RealSyncAgent",
                    "module": "twisterlab.agents.real.real_sync_agent",
                    "file": "src/twisterlab/agents/real/real_sync_agent.py",
                    "mcp_tool": "sync_cache_db",
                    "description": "Cache/Database synchronization (Redis ↔ PostgreSQL)",
                    "capabilities": [
                        "redis_sync",
                        "postgres_sync",
                        "conflict_resolution",
                    ],
                    "status": "operational",
                },
                {
                    "name": "RealClassifierAgent",
                    "module": "twisterlab.agents.real.real_classifier_agent",
                    "file": "src/twisterlab/agents/real/real_classifier_agent.py",
                    "mcp_tool": "classify_ticket",
                    "description": "Ticket classification using Ollama LLM (llama3.2:1b)",
                    "capabilities": [
                        "llm_classification",
                        "confidence_scoring",
                        "priority_assignment",
                    ],
                    "categories": [
                        "network",
                        "hardware",
                        "software",
                        "account",
                        "email",
                    ],
                    "status": "operational",
                },
                {
                    "name": "RealResolverAgent",
                    "module": "twisterlab.agents.real.real_resolver_agent",
                    "file": "src/twisterlab/agents/real/real_resolver_agent.py",
                    "mcp_tool": "resolve_ticket",
                    "description": "SOP-based ticket resolution (network, hardware, software, account, email)",
                    "capabilities": [
                        "sop_execution",
                        "troubleshooting",
                        "guided_resolution",
                    ],
                    "status": "operational",
                },
                {
                    "name": "RealDesktopCommanderAgent",
                    "module": "twisterlab.agents.real.real_desktop_commander_agent",
                    "file": "src/twisterlab/agents/real/real_desktop_commander_agent.py",
                    "mcp_tool": "execute_command",
                    "description": "Remote system command execution (PowerShell, Bash, SSH)",
                    "capabilities": [
                        "powershell_execution",
                        "bash_execution",
                        "ssh_commands",
                        "command_whitelisting",
                    ],
                    "status": "operational",
                    "security": "whitelisted_commands_only",
                },
                {
                    "name": "RealMaestroAgent",
                    "module": "twisterlab.agents.real.real_maestro_agent",
                    "file": "src/twisterlab/agents/real/real_maestro_agent.py",
                    "mcp_tool": None,
                    "description": "Workflow orchestration and load balancing (agent coordination)",
                    "capabilities": [
                        "workflow_orchestration",
                        "load_balancing",
                        "state_persistence",
                        "error_recovery",
                    ],
                    "status": "operational",
                },
                {
                    "name": "SentimentAnalyzerAgent",
                    "module": "twisterlab.agents.real.real_sentiment_analyzer_agent",
                    "file": "src/twisterlab/agents/real/real_sentiment_analyzer_agent.py",
                    "mcp_tool": "analyze_sentiment",
                    "description": "Text sentiment analysis with multilingual support (EN, FR, ES, DE)",
                    "capabilities": [
                        "sentiment_detection",
                        "confidence_scoring",
                        "keyword_extraction",
                        "multilingual_support",
                    ],
                    "supported_languages": ["en", "fr", "es", "de"],
                    "status": "operational",
                },
            ],
            "infrastructure": {
                "database": "PostgreSQL 16",
                "cache": "Redis 7",
                "llm": "Ollama (llama3.2:1b, llama3:latest)",
                "deployment": "Kubernetes",
                "monitoring": "Prometheus + Grafana",
            },
            "api_base": "http://192.168.0.30:8000",
            "mcp_protocol": "2024-11-05",
        }

        logger.info("list_autonomous_agents called - returning 8 agents")
        return MCPResponse(status="ok", data=agents_data)

    except Exception as e:
        logger.error(f"Error in list_autonomous_agents: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


# ============================================================================
# PYDANTIC MODELS - Input Validation
# ============================================================================


class ClassifyTicketRequest(BaseModel):
    """Input model for classify_ticket endpoint."""

    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Ticket description (min 10 chars)",
    )
    priority: Optional[str] = Field(
        None,
        pattern="^(critical|high|medium|low)$",
        description="Optional manual priority override",
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        """Ensure description is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip()


class ResolveTicketRequest(BaseModel):
    """Input model for resolve_ticket endpoint."""

    ticket_id: Optional[int] = Field(None, gt=0, description="Ticket ID (optional)")
    category: str = Field(
        ...,
        pattern="^(network|software|hardware|security|performance|database)$",
        description="Ticket category",
    )
    description: Optional[str] = Field(
        None, max_length=5000, description="Ticket description for context"
    )


class MonitorSystemHealthRequest(BaseModel):
    """Input model for monitor_system_health endpoint."""

    detailed: Optional[bool] = Field(
        False, description="Return detailed metrics (CPU, RAM, disk, services)"
    )


class CreateBackupRequest(BaseModel):
    """Input model for create_backup endpoint."""

    backup_type: str = Field(
        "full", pattern="^(full|incremental|config)$", description="Backup type"
    )


class SyncCacheDBRequest(BaseModel):
    """Input model for sync_cache_db endpoint."""

    operation: str = Field(
        "sync_all",
        pattern="^(sync_all|verify_consistency|clear_stale|warm_cache)$",
        description="Sync operation to perform",
    )
    force: Optional[bool] = Field(
        False, description="Force sync even if cache is fresh"
    )


class ExecuteCommandRequest(BaseModel):
    """Input model for execute_command endpoint."""

    command: str = Field(
        ...,
        pattern="^(ping|ipconfig|netstat|systeminfo|tasklist|whoami|hostname|route|nslookup)$",
        description="Safe whitelisted command to execute",
    )
    args: Optional[List[str]] = Field(None, description="Optional command arguments")
    target: Optional[str] = Field(
        None, description="Target for network commands (IP/hostname)"
    )


class BrowseWebRequest(BaseModel):
    """Input model for browse_web endpoint."""

    url: str = Field(..., description="URL to visit (http/https)")
    screenshot: Optional[bool] = Field(
        True, description="Take a screenshot of the page"
    )

class AnalyzeCodeRequest(BaseModel):
    """Input model for analyze_code endpoint."""
    code: str = Field(..., description="Code snippet to analyze")
    language: str = Field("python", description="Programming language")


# ============================================================================
# ENDPOINTS - MCP Tool Routes
# ============================================================================


@router.post("/classify_ticket", response_model=MCPResponse)
@router.post("/twisterlab_mcp_classify_ticket", response_model=MCPResponse)
async def classify_ticket(
    request: ClassifyTicketRequest,
    session: Optional[AsyncSession] = Depends(get_db_session),
) -> MCPResponse:
    """
    Classify a helpdesk ticket using RealClassifierAgent.

    **Database Integration**: Creates ticket record and logs execution (graceful fallback if DB down).

    **Input**:
    - `description`: Ticket description (10-5000 chars)
    - `priority`: Optional priority override (critical|high|medium|low)

    **Output**:
    - `status`: "ok" or "error"
    - `data`: Classification results + ticket_id from database (if available)
    - `error`: Error message if status="error"

    **Example**:
    ```json
    POST /v1/mcp/tools/classify_ticket
    {
        "description": "WiFi connection keeps dropping every few minutes",
        "priority": null
    }

    Response:
    {
        "status": "ok",
        "data": {
            "category": "network",
            "subcategory": "wifi",
            "confidence": 0.92,
            "priority": "high",
            "routed_to": "DesktopCommanderAgent",
            "method": "llm",
            "ticket_id": 123
        },
        "error": null,
        "timestamp": "2025-11-11T12:00:00.000000+00:00"
    }
    ```
    """
    ticket_id = None
    try:
        logger.info(f"🔍 Classifying ticket: {request.description[:50]}...")
        start_time = time.time()

        # 1. Try to save to database (with fallback if DB is down)
        if session:
            try:
                ticket_repo = TicketRepository(session)
                log_repo = AgentLogRepository(session)

                # Create ticket in database
                priority_enum = (
                    TicketPriority(request.priority)
                    if request.priority
                    else TicketPriority.MEDIUM
                )
                ticket_db = await ticket_repo.create(
                    description=request.description, priority=priority_enum
                )
                ticket_id = ticket_db.id
                logger.info(f"✅ Ticket saved to database: ticket_id={ticket_id}")
            except Exception as db_error:
                logger.warning(
                    f"⚠️ Database unavailable, continuing without persistence: {db_error}"
                )
                session = None  # Disable DB for rest of request
        else:
            logger.warning(
                "⚠️ Database session not available, classification will not be persisted"
            )

        # 2. Initialize agent
        agent = RealClassifierAgent()

        # Build ticket context
        ticket = {
            "id": ticket_id,  # Include DB ticket ID if available
            "description": request.description,
            "title": request.description[:100],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 3. Execute classification
        result = await agent.execute({"operation": "classify_ticket", "ticket": ticket})

        # Check if classification succeeded
        if result.get("status") != "success":
            error_msg = result.get("error", "Unknown error")
            logger.error(f"❌ Classification failed: {error_msg}")

            # Try to log failure to database
            if session and ticket_id:
                try:
                    await log_repo.log_execution(
                        agent_name="RealClassifierAgent",
                        action="classify_ticket",
                        ticket_id=ticket_id,
                        error=error_msg,
                    )
                    await session.commit()
                except Exception as log_error:
                    logger.warning(f"⚠️ Failed to log error to database: {log_error}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Classification failed: {error_msg}",
            )

        # Extract classification data
        classification = result.get("classification", {})

        # Override priority if provided
        if request.priority:
            classification["priority"] = request.priority

        # 4. Update database (if available)
        execution_time_ms = int((time.time() - start_time) * 1000)
        if session and ticket_id:
            try:
                category = classification.get("category", "unknown")
                await ticket_repo.update_category(ticket_id, category)

                # Log successful execution
                await log_repo.log_execution(
                    agent_name="RealClassifierAgent",
                    action="classify_ticket",
                    ticket_id=ticket_id,
                    result=classification,
                    execution_time_ms=execution_time_ms,
                )

                # Commit transaction
                await session.commit()
                logger.info(
                    f"✅ Database updated: category={category}, execution_time={execution_time_ms}ms"
                )
            except Exception as db_error:
                logger.warning(f"⚠️ Failed to update database: {db_error}")
                # Continue anyway - classification succeeded even if DB update failed

        logger.info(
            f"✅ Classification complete: {classification.get('category')} "
            f"(confidence: {classification.get('confidence')}) "
            f"[ticket_id={ticket_id}, {execution_time_ms}ms]"
        )

        return MCPResponse(
            status="ok",
            data={
                **classification,
                "ticket_id": ticket_id,  # Will be None if DB is down
                "execution_time_ms": execution_time_ms,
                "database_persisted": ticket_id is not None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ classify_ticket failed: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


@router.post("/resolve_ticket", response_model=MCPResponse)
@router.post("/twisterlab_mcp_resolve_ticket", response_model=MCPResponse)
async def resolve_ticket(request: ResolveTicketRequest) -> MCPResponse:
    """
    Resolve a ticket using RealResolverAgent (executes SOPs).

    **Input**:
    - `ticket_id`: Optional ticket ID
    - `category`: Ticket category (network|software|hardware|security|performance|database)
    - `description`: Optional description for context

    **Output**:
    - `status`: "ok" or "error"
    - `data`: Resolution steps, SOP executed, estimated time
    - `error`: Error message if status="error"

    **Example**:
    ```json
    POST /v1/mcp/tools/resolve_ticket
    {
        "ticket_id": 123,
        "category": "network",
        "description": "WiFi not working"
    }

    Response:
    {
        "status": "ok",
        "data": {
            "sop_executed": "network_troubleshoot",
            "steps": [
                "Check physical connection (cables, WiFi signal)",
                "Ping localhost (127.0.0.1) to verify network stack",
                "Ping gateway to verify local network",
                "Ping external DNS (8.8.8.8) to verify internet",
                "Check DNS resolution with nslookup",
                "Restart network adapter if needed"
            ],
            "estimated_time": "15 minutes",
            "success_rate": 0.85,
            "method": "static_sop"
        },
        "error": null,
        "timestamp": "2025-11-11T12:00:00.000000+00:00"
    }
    ```
    """
    try:
        logger.info(
            f"🔧 Resolving ticket (category: {request.category}, ID: {request.ticket_id})"
        )

        # Initialize agent
        agent = RealResolverAgent()

        # Build ticket context
        ticket = {
            "category": request.category,
            "description": request.description or f"Ticket #{request.ticket_id}",
            "ticket_id": request.ticket_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Execute resolution
        result = await agent.execute({"operation": "resolve_ticket", "ticket": ticket})

        # Check if resolution succeeded
        if result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Resolution failed: {result.get('error', 'Unknown error')}",
            )

        # Extract resolution data
        resolution = result.get("resolution", {})

        logger.info(
            f"✅ Resolution complete: SOP {resolution.get('sop_id')} "
            f"({len(resolution.get('steps', []))} steps)"
        )

        return MCPResponse(status="ok", data=resolution)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ resolve_ticket failed: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


@router.post("/monitor_system_health", response_model=MCPResponse)
async def monitor_system_health(
    request: MonitorSystemHealthRequest, session: AsyncSession = Depends(get_db_session)
) -> MCPResponse:
    """
    Monitor system health using RealMonitoringAgent.

    **Input**:
    - `detailed`: Return detailed metrics (default: false)

    **Output**:
    - `status`: "ok" or "error"
    - `data`: System health metrics (CPU, RAM, disk, services, ports)
    - `error`: Error message if status="error"

    **Example**:
    ```json
    POST /v1/mcp/tools/monitor_system_health
    {
        "detailed": true
    }

    Response:
    {
        "status": "ok",
        "data": {
            "overall_status": "healthy",
            "cpu_percent": 45.2,
            "memory_percent": 62.1,
            "disk_percent": 38.5,
            "services": {
                "twisterlab_api": "running",
                "twisterlab_postgres": "running",
                "twisterlab_redis": "running"
            },
            "alerts": [],
            "uptime_hours": 168.5
        },
        "error": null,
        "timestamp": "2025-11-11T12:00:00.000000+00:00"
    }
    ```
    """
    try:
        logger.info(f"🏥 Monitoring system health (detailed: {request.detailed})")
        start_time = time.time()

        # Initialize repositories
        # metrics_repo reserved for future metrics collection
        log_repo = AgentLogRepository(session)

        # Initialize agent
        agent = RealMonitoringAgent()

        # Execute health check
        result = await agent.execute(
            {"operation": "health_check", "detailed": request.detailed}
        )

        # Check if health check succeeded
        if result.get("status") != "success":
            # Log failure
            await log_repo.log_execution(
                agent_name="RealMonitoringAgent",
                action="health_check",
                error=result.get("error", "Unknown error"),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Health check failed: {result.get('error', 'Unknown error')}",
            )

        # Extract health data
        health_data = result.get("health_check", {})
        health_data["overall_status"] = result.get("health_status", "unknown")
        health_data["issues"] = result.get("issues", [])

        # Record metrics in database
        cpu = health_data.get("cpu_percent", 0.0)
        memory = health_data.get("memory_percent", 0.0)
        disk = health_data.get("disk_percent", 0.0)
        docker_status = health_data.get("overall_status", "unknown")

        # TODO: Re-enable database metrics recording
        # await metrics_repo.record_metrics(
        #     cpu_usage=cpu, memory_usage=memory, disk_usage=disk, docker_status=docker_status
        # )

        # Log execution
        execution_time_ms = int((time.time() - start_time) * 1000)
        # TODO: Re-enable database logging
        # await log_repo.log_execution(
        #     agent_name="RealMonitoringAgent",
        #     action="health_check",
        #     result={"status": docker_status, "cpu": cpu, "memory": memory, "disk": disk},
        #     execution_time_ms=execution_time_ms,
        # )

        # Commit transaction
        # TODO: Re-enable database commit
        # await session.commit()

        logger.info(
            f"✅ Health check complete: {docker_status} "
            f"(CPU: {cpu}%, RAM: {memory}%, Disk: {disk}%) [{execution_time_ms}ms]"
        )

        return MCPResponse(
            status="ok", data={**health_data, "execution_time_ms": execution_time_ms}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ monitor_system_health failed: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


@router.post("/create_backup", response_model=MCPResponse)
async def create_backup(request: CreateBackupRequest) -> MCPResponse:
    """
    Create system backup using RealBackupAgent.

    **Input**:
    - `backup_type`: Backup type (full|incremental|config)

    **Output**:
    - `status`: "ok" or "error"
    - `data`: Backup details (backup_id, path, size, checksum)
    - `error`: Error message if status="error"

    **Example**:
    ```json
    POST /v1/mcp/tools/create_backup
    {
        "backup_type": "full"
    }

    Response:
    {
        "status": "ok",
        "data": {
            "backup_id": "20251111_120000",
            "backup_name": "twisterlab_backup_20251111_120000.tar.gz",
            "backup_type": "full",
            "path": "/var/backups/twisterlab/20251111_120000.tar.gz",
            "size_bytes": 524288000,
            "size_mb": 500.0,
            "checksum": "a3f5d8c2b1e9...",
            "components": ["database", "redis", "config"],
            "duration_seconds": 45.3
        },
        "error": null,
        "timestamp": "2025-11-11T12:00:00.000000+00:00"
    }
    ```
    """
    try:
        logger.info(f"💾 Creating backup (type: {request.backup_type})")

        # Initialize agent
        agent = RealBackupAgent()

        # Execute backup
        result = await agent.execute(
            {"operation": "create_backup", "backup_type": request.backup_type}
        )

        # Check if backup succeeded
        if result.get("status") not in ["success", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Backup failed: {result.get('error', 'Unknown error')}",
            )

        # Extract backup data
        backup = result.get("backup", result)  # Handle different response formats

        logger.info(
            f"✅ Backup complete: {backup.get('backup_id')} "
            f"({backup.get('size_mb', 0)}MB in {backup.get('duration_seconds', 0)}s)"
        )

        return MCPResponse(status="ok", data=backup)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ create_backup failed: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


@router.post("/sync_cache_db", response_model=MCPResponse)
@router.post("/twisterlab_mcp_sync_cache", response_model=MCPResponse)
async def sync_cache_db(request: SyncCacheDBRequest) -> MCPResponse:
    """
    Synchronize Redis cache with PostgreSQL database using RealSyncAgent.

    **Input**:
    - `operation`: Sync operation (sync_all|verify_consistency|clear_stale|warm_cache)
    - `force`: Force sync even if cache is fresh (default: false)

    **Output**:
    - `status`: "ok" or "error"
    - `data`: Sync results with statistics (entries synced, duration, etc.)
    - `error`: Error message if status="error"

    **Example**:
    ```json
    POST /v1/mcp/tools/sync_cache_db
    {
        "operation": "sync_all",
        "force": true
    }

    Response:
    {
        "status": "ok",
        "data": {
            "operation": "sync_all",
            "entries_synced": 150,
            "duration_seconds": 2.3,
            "cache_entries_before": 120,
            "cache_entries_after": 180,
            "db_records_processed": 200
        },
        "error": null,
        "timestamp": "2025-11-11T12:00:00.000000+00:00"
    }
    ```
    """
    try:
        logger.info(
            f"🔄 Syncing cache/DB (operation: {request.operation}, force: {request.force})"
        )

        # Initialize agent
        agent = RealSyncAgent()

        # Execute sync
        result = await agent.execute(
            {"operation": request.operation, "force": request.force}
        )

        # Check if sync succeeded
        if result.get("status") not in ["success", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sync failed: {result.get('error', 'Unknown error')}",
            )

        # Extract sync data
        sync_data = result

        logger.info(
            f"✅ Sync complete: {request.operation} "
            f"({sync_data.get('entries_synced', 0)} entries in {sync_data.get('duration_seconds', 0)}s)"
        )

        return MCPResponse(status="ok", data=sync_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ sync_cache_db failed: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


@router.post("/execute_command", response_model=MCPResponse)
async def execute_command(request: ExecuteCommandRequest) -> MCPResponse:
    """
    Execute safe system command using RealDesktopCommanderAgent.

    **Security**: Only whitelisted commands allowed (ping, ipconfig, netstat, etc.)

    **Input**:
    - `command`: Whitelisted command to execute
    - `args`: Optional command arguments
    - `target`: Target for network commands (IP/hostname)

    **Output**:
    - `status`: "ok" or "error"
    - `data`: Command output, execution time, security validation
    - `error`: Error message if status="error"

    **Example**:
    ```json
    POST /v1/mcp/tools/execute_command
    {
        "command": "ping",
        "args": ["-n", "4"],
        "target": "8.8.8.8"
    }

    Response:
    {
        "status": "ok",
        "data": {
            "command": "ping",
            "output": "Pinging 8.8.8.8 with 32 bytes of data:\nReply from 8.8.8.8: bytes=32 time=14ms TTL=118\n...",
            "execution_time_seconds": 3.2,
            "security_validated": true,
            "os_type": "Windows"
        },
        "error": null,
        "timestamp": "2025-11-11T12:00:00.000000+00:00"
    }
    ```
    """
    try:
        logger.info(
            f"💻 Executing command: {request.command} (args: {request.args}, target: {request.target})"
        )

        # Initialize agent
        agent = RealDesktopCommanderAgent()

        # Execute command
        result = await agent.execute(
            {
                "operation": "execute_command",
                "command": request.command,
                "args": request.args,
                "target": request.target,
            }
        )

        # Check if command succeeded
        if result.get("status") not in ["success", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Command failed: {result.get('error', 'Unknown error')}",
            )

        # Extract command data
        command_data = result  # The result is already the command data dict

        logger.info(
            f"✅ Command complete: {request.command} "
            f"(executed in {command_data.get('execution_time_seconds', 0)}s)"
        )

        return MCPResponse(status="ok", data=command_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ execute_command failed: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


# ============================================================================
# SENTIMENT ANALYSIS - Analyze Text Sentiment
# ============================================================================


class AnalyzeSentimentRequest(BaseModel):
    """Request model for sentiment analysis."""

    text: str = Field(..., description="Text to analyze for sentiment")
    detailed: bool = Field(
        default=False, description="Return detailed analysis with keyword extraction"
    )


@router.post("/analyze_sentiment", response_model=MCPResponse)
async def analyze_sentiment(request: AnalyzeSentimentRequest) -> MCPResponse:
    """
    Analyze text sentiment using SentimentAnalyzerAgent.

    **Input**:
    - `text`: Text to analyze for sentiment
    - `detailed`: Return detailed analysis (default: false)

    **Output**:
    - `status`: "ok" or "error"
    - `data`: Sentiment analysis results (sentiment, confidence, keywords if detailed)
    - `error`: Error message if status="error"

    **Example**:
    ```json
    POST /v1/mcp/tools/analyze_sentiment
    {
        "text": "This is an excellent product! I love it and it works perfectly.",
        "detailed": true
    }

    Response:
    {
        "status": "ok",
        "data": {
            "sentiment": "positive",
            "confidence": 0.85,
            "keywords": ["excellent", "love", "perfectly"],
            "language": "en",
            "text_length": 65,
            "timestamp": "2025-12-11T15:30:00.000000+00:00"
        },
        "error": null,
        "timestamp": "2025-12-11T15:30:00.000000+00:00"
    }
    ```
    """
    try:
        logger.info(f"🎭 Analyzing sentiment for text (length: {len(request.text)})")
        start_time = time.time()

        # Initialize agent
        agent = SentimentAnalyzerAgent()

        # Execute sentiment analysis using capability name
        result = await agent.execute(
            "analyze_sentiment", 
            text=request.text, 
            detailed=request.detailed
        )

        # Check if analysis succeeded
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sentiment analysis failed: {result.error or 'Unknown error'}",
            )

        # Extract sentiment data from AgentResponse
        result_data = result.data if isinstance(result.data, dict) else {}
        sentiment_data = {
            "sentiment": result_data.get("sentiment", "unknown"),
            "confidence": result_data.get("confidence", 0.0),
            "text_length": len(request.text),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add detailed data if requested
        if request.detailed:
            sentiment_data["keywords"] = result_data.get("keywords", [])

        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"✅ Sentiment analysis completed in {execution_time_ms}ms: {sentiment_data['sentiment']} ({sentiment_data['confidence']:.2f})"
        )

        return MCPResponse(status="ok", data=sentiment_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ analyze_sentiment failed: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


# ============================================================================
# HEALTH CHECK - MCP Service Status
# ============================================================================


@router.get("/health")
async def mcp_health() -> Dict[str, Any]:
    """
    MCP service health check.

    Returns:
        Service status, mode, available tools count
    """
    return {
        "status": "ok",
        "mode": "REAL",
        "tools": 7,
        "tools_available": [
            "classify_ticket",
            "resolve_ticket",
            "monitor_system_health",
            "create_backup",
            "sync_cache_db",
            "execute_command",
            "analyze_sentiment",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# BROWSER - Web Automation
# ============================================================================


@router.post("/browse_web", response_model=MCPResponse)
async def browse_web(request: BrowseWebRequest) -> MCPResponse:
    """
    Browse a web page using RealBrowserAgent (Playwright).
    
    **Input**:
    - `url`: URL to visit
    - `screenshot`: Take screenshot (default: true)
    
    **Output**:
    - Page title, content preview, screenshot (base64)
    """
    try:
        logger.info(f"🌐 Browsing web: {request.url}")
        
        agent = RealBrowserAgent()
        result = await agent.execute(
            {"operation": "browse", "url": request.url, "screenshot": request.screenshot}
        )
        
        if not result.success:
             return MCPResponse(status="error", error=result.error)
             
        return MCPResponse(status="ok", data=result.data)

    except Exception as e:
        logger.error(f"Browse error: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


# ============================================================================
# CODE ANALYSIS - Review & Security
# ============================================================================


@router.post("/analyze_code", response_model=MCPResponse)
async def analyze_code(request: AnalyzeCodeRequest) -> MCPResponse:
    """
    Analyze code using RealCodeReviewAgent.
    """
    try:
        logger.info(f"🧐 Analyzing code ({request.language})")
        
        agent = RealCodeReviewAgent()
        result = await agent.execute(
            {"operation": "analyze_code", "code": request.code, "language": request.language}
        )
        
        if not result.success:
             return MCPResponse(status="error", error=result.error)
             
        return MCPResponse(status="ok", data=result.data)

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


# ============================================================================
# MAESTRO ORCHESTRATION - Multi-Agent Coordination
# ============================================================================


class OrchestrateRequest(BaseModel):
    """Input model for orchestrate endpoint."""

    task: str = Field(
        ...,
        min_length=5,
        max_length=5000,
        description="Task/ticket description to process",
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context (priority, metadata, etc.)",
    )
    dry_run: bool = Field(
        default=False,
        description="If true, plan only without execution",
    )


class AnalyzeTaskRequest(BaseModel):
    """Input model for analyze_task endpoint."""

    task: str = Field(
        ...,
        min_length=5,
        max_length=5000,
        description="Task/ticket description to analyze",
    )


@router.post("/orchestrate", response_model=MCPResponse)
async def orchestrate(request: OrchestrateRequest) -> MCPResponse:
    """
    Orchestrate a multi-agent workflow using RealMaestroAgent.
    
    This is the main entry point for autonomous incident resolution.
    Maestro will:
    1. Analyze the task (LLM or rule-based)
    2. Create a multi-step plan
    3. Dispatch specialized agents
    4. Synthesize results
    
    Args:
        request: OrchestrateRequest with task, context, and dry_run flag
        
    Returns:
        MCPResponse with orchestration results
    """
    from twisterlab.agents.registry import agent_registry
    
    try:
        logger.info(f"🧠 Maestro orchestration: {request.task[:50]}...")
        
        maestro = agent_registry.get_agent("maestro")
        if not maestro:
            return MCPResponse(
                status="error",
                error="Maestro agent not found in registry"
            )
        
        result = await maestro.execute(
            "orchestrate",
            task=request.task,
            context=request.context,
            dry_run=request.dry_run
        )
        
        if not result.success:
            return MCPResponse(status="error", error=result.error)
        
        return MCPResponse(status="ok", data=result.data)

    except Exception as e:
        logger.error(f"Orchestration error: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))


@router.post("/analyze_task", response_model=MCPResponse)
async def analyze_task(request: AnalyzeTaskRequest) -> MCPResponse:
    """
    Analyze a task to determine category, priority, and suggested agents.
    
    This is a lightweight endpoint for task classification without execution.
    
    Args:
        request: AnalyzeTaskRequest with task description
        
    Returns:
        MCPResponse with analysis (category, priority, suggested_agents)
    """
    from twisterlab.agents.registry import agent_registry
    
    try:
        logger.info(f"🔍 Task analysis: {request.task[:50]}...")
        
        maestro = agent_registry.get_agent("maestro")
        if not maestro:
            return MCPResponse(
                status="error",
                error="Maestro agent not found in registry"
            )
        
        result = await maestro.execute("analyze_task", task=request.task)
        
        if not result.success:
            return MCPResponse(status="error", error=result.error)
        
        return MCPResponse(status="ok", data=result.data)

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return MCPResponse(status="error", error=str(e))

