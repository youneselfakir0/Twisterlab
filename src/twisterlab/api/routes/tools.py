"""
Dynamic MCP Tools Router

Exposes all agent capabilities as /tools/{agent}_{capability} endpoints.
Uses the unified ToolRouter for execution.

Security Features:
- Router-level authentication dependency
- RBAC with role-based access control
- Comprehensive audit logging for compliance
- Caching for performance
- Environment-based configuration
"""

import logging
import threading
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, ConfigDict

from twisterlab.api.auth import get_current_user
from twisterlab.agents.mcp.router import ToolRouter, AgentRegistry
from twisterlab.agents.registry import agent_registry as main_registry

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration via Environment Variables
# =============================================================================

class ToolsConfig:
    """Configuration for tools router loaded from environment."""
    
    def __init__(self):
        import os
        
        # RBAC Configuration (comma-separated roles)
        self.rbac_backup_roles = self._parse_roles(os.getenv("RBAC_BACKUP_ROLES", "Admin"))
        self.rbac_resolver_roles = self._parse_roles(os.getenv("RBAC_RESOLVER_ROLES", "Admin,Support"))
        self.rbac_classifier_roles = self._parse_roles(os.getenv("RBAC_CLASSIFIER_ROLES", "Viewer,Support,Admin"))
        self.rbac_sentiment_roles = self._parse_roles(os.getenv("RBAC_SENTIMENT_ROLES", "Viewer,Support,Admin"))
        self.rbac_maestro_roles = self._parse_roles(os.getenv("RBAC_MAESTRO_ROLES", "Admin"))
        self.rbac_database_roles = self._parse_roles(os.getenv("RBAC_DATABASE_ROLES", "Admin"))
        self.rbac_code_review_roles = self._parse_roles(os.getenv("RBAC_CODE_REVIEW_ROLES", "Admin,Operator,Support"))
        self.rbac_monitoring_roles = self._parse_roles(os.getenv("RBAC_MONITORING_ROLES", "Viewer,Support,Admin"))
        self.rbac_browser_roles = self._parse_roles(os.getenv("RBAC_BROWSER_ROLES", "Admin,Operator"))
        self.rbac_commander_roles = self._parse_roles(os.getenv("RBAC_COMMANDER_ROLES", "Admin"))
        
        # Feature flags
        self.audit_logging_enabled = os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true"
        self.cache_tool_schemas = os.getenv("CACHE_TOOL_SCHEMAS", "true").lower() == "true"
    
    @staticmethod
    def _parse_roles(roles_str: str) -> List[str]:
        """Parse comma-separated roles string."""
        return [r.strip() for r in roles_str.split(",") if r.strip()]


# Global configuration (singleton)
config = ToolsConfig()

# Build permissions dict from config
TOOL_PERMISSIONS: Dict[str, List[str]] = {
    "real-backup": config.rbac_backup_roles,
    "real-resolver": config.rbac_resolver_roles,
    "real-classifier": config.rbac_classifier_roles,
    "sentiment-analyzer": config.rbac_sentiment_roles,
    "maestro": config.rbac_maestro_roles,
    "database": config.rbac_database_roles,
    "code-review": config.rbac_code_review_roles,
    "monitoring": config.rbac_monitoring_roles,
    "browser": config.rbac_browser_roles,
    "real-desktop-commander": config.rbac_commander_roles,
}

# =============================================================================
# Global State with Thread Safety
# =============================================================================

_tool_router: Optional[ToolRouter] = None
_router_lock = threading.Lock()
_initialized = False


def initialize_tool_router() -> ToolRouter:
    """
    Initialize the ToolRouter with all agents from the main registry.
    Thread-safe initialization.
    """
    global _tool_router, _initialized
    
    if _initialized and _tool_router is not None:
        return _tool_router
    
    with _router_lock:
        if _initialized and _tool_router is not None:
            return _tool_router
        
        logger.info("Initializing ToolRouter...")
        
        # Create MCP AgentRegistry and populate from main registry
        mcp_registry = AgentRegistry()
        
        registered_count = 0
        for agent_name, agent in main_registry._agents.items():
            if hasattr(agent, 'list_capabilities') or hasattr(agent, 'get_capabilities'):
                try:
                    mcp_registry.register_instance(agent)
                    registered_count += 1
                    logger.debug(f"Registered agent for tools: {agent_name}")
                except Exception as e:
                    logger.warning(f"Could not register agent {agent_name}: {e}")
        
        _tool_router = ToolRouter(mcp_registry)
        _initialized = True
        
        tool_count = len(_tool_router.list_tools())
        logger.info(f"ToolRouter initialized with {tool_count} tools from {registered_count} agents")
        
        return _tool_router


def get_tool_router() -> ToolRouter:
    """Get the global ToolRouter instance. Initializes lazily if needed."""
    global _tool_router
    
    if _tool_router is None:
        return initialize_tool_router()
    
    return _tool_router


# =============================================================================
# Audit Logging
# =============================================================================

def audit_log(event: str, user: dict, details: Optional[dict] = None) -> None:
    """Log security-relevant events for compliance."""
    if not config.audit_logging_enabled:
        return
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "user_id": user.get("sub", "anonymous"),
        "user_roles": user.get("roles", []),
        "details": details or {}
    }
    logger.info(f"AUDIT: {log_entry}")


# =============================================================================
# RBAC Functions
# =============================================================================

def _get_required_roles(tool_name: str) -> Optional[List[str]]:
    """Extract required roles for a tool name based on prefix matching."""
    for prefix, roles in TOOL_PERMISSIONS.items():
        if tool_name.startswith(prefix):
            return roles
    return None


def _check_tool_permission(tool_name: str, user: dict) -> None:
    """Verify user has required role for the tool. Raises 403 if unauthorized."""
    user_roles = user.get("roles", [])
    required_roles = _get_required_roles(tool_name)
    
    if required_roles:
        if not any(role in user_roles for role in required_roles):
            audit_log("tool_access_denied", user, {
                "tool": tool_name,
                "required_roles": required_roles,
                "user_roles": user_roles
            })
            raise HTTPException(
                status_code=403,
                detail=f"Access Denied. Required roles: {', '.join(required_roles)}"
            )
    
    logger.debug(f"Tool access granted: {tool_name} for user {user.get('sub')}")


# =============================================================================
# Pydantic Models with Validation
# =============================================================================

class ToolRequest(BaseModel):
    """Request model for tool execution with validation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "arguments": {
                    "text": "Analyze this message for sentiment",
                    "detailed": True
                }
            }
        }
    )
    
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific arguments as key-value pairs"
    )
    
    @field_validator('arguments')
    @classmethod
    def validate_arguments(cls, v):
        """Ensure arguments is a valid dictionary."""
        if not isinstance(v, dict):
            raise ValueError('arguments must be a dictionary')
        if len(str(v)) > 100000:
            raise ValueError('arguments payload too large (max 100KB)')
        return v


class ToolResponse(BaseModel):
    """Response model for tool execution."""
    content: List[Dict[str, Any]] = Field(default_factory=list)
    isError: bool = Field(default=False)


class ToolInfo(BaseModel):
    """Metadata about a single tool."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class ToolListResponse(BaseModel):
    """Response for listing tools."""
    tools: List[Dict[str, Any]]
    count: int
    total: int
    filtered: bool = True


class RouterStats(BaseModel):
    """Router statistics response."""
    total_agents: int
    total_tools: int
    avg_latency_seconds: float
    recent_executions: int
    error_count_recent: int
    agents: List[Dict[str, Any]]
    timestamp: str


# =============================================================================
# Router with Authentication Dependency
# =============================================================================

router = APIRouter(
    tags=["tools"],
    dependencies=[Depends(get_current_user)]
)


# =============================================================================
# Cached Schema Lookup
# =============================================================================

@lru_cache(maxsize=256)
def _get_cached_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get tool schema with caching for performance."""
    tool_router = get_tool_router()
    return tool_router.get_tool(tool_name)


def _clear_schema_cache():
    """Clear the schema cache (call when agents are added/removed)."""
    _get_cached_tool_schema.cache_clear()


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("", response_model=ToolListResponse)
async def list_all_tools(user: dict = Depends(get_current_user)):
    """List all available MCP tools. Returns only tools the user has permission to access."""
    tool_router = get_tool_router()
    all_tools = tool_router.list_tools()
    user_roles = user.get("roles", [])
    
    accessible_tools = []
    for tool in all_tools:
        tool_name = tool.get("name", "")
        required_roles = _get_required_roles(tool_name)
        
        if not required_roles or any(role in user_roles for role in required_roles):
            accessible_tools.append(tool)
    
    return ToolListResponse(
        tools=accessible_tools,
        count=len(accessible_tools),
        total=len(all_tools),
        filtered=len(accessible_tools) < len(all_tools)
    )


@router.post("/{tool_name}", response_model=ToolResponse)
async def execute_tool(
    tool_name: str,
    request: ToolRequest,
    user: dict = Depends(get_current_user)
):
    """
    Execute an MCP tool by name with RBAC and audit logging.
    
    Tool names follow the pattern: `{agent_name}_{capability_name}`
    
    Examples:
    - `real-classifier_classify_ticket`
    - `sentiment-analyzer_analyze_sentiment`
    - `code-review_security_scan`
    - `monitoring_collect_metrics`
    """
    tool_router = get_tool_router()
    
    # Check if tool exists
    if not tool_router.can_handle(tool_name):
        available = [t["name"] for t in tool_router.list_tools()]
        audit_log("tool_not_found", user, {"tool": tool_name})
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. {len(available)} tools available."
        )
    
    # RBAC Check
    _check_tool_permission(tool_name, user)
    
    # Execute tool
    try:
        audit_log("tool_execution_started", user, {
            "tool": tool_name,
            "arguments_keys": list(request.arguments.keys())
        })
        
        result = await tool_router.execute_tool(tool_name, request.arguments)
        
        if result.get("isError"):
            error_msg = result.get("content", [{"text": "Unknown error"}])[0].get("text", "Unknown error")
            audit_log("tool_execution_failed", user, {"tool": tool_name, "error": error_msg})
            raise HTTPException(status_code=400, detail=error_msg)
        
        audit_log("tool_execution_success", user, {"tool": tool_name})
        return ToolResponse(
            content=result.get("content", []),
            isError=result.get("isError", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        audit_log("tool_execution_exception", user, {"tool": tool_name, "exception": str(e)})
        logger.exception(f"Error executing tool {tool_name}")
        raise HTTPException(status_code=500, detail="Internal server error during tool execution")


@router.get("/{tool_name}/schema", response_model=ToolInfo)
async def get_tool_schema(tool_name: str, user: dict = Depends(get_current_user)):
    """Get the input schema for a specific tool. Results are cached."""
    _check_tool_permission(tool_name, user)
    
    if config.cache_tool_schemas:
        tool = _get_cached_tool_schema(tool_name)
    else:
        tool_router = get_tool_router()
        tool = tool_router.get_tool(tool_name)
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return ToolInfo(
        name=tool.get("name", tool_name),
        description=tool.get("description", ""),
        inputSchema=tool.get("inputSchema", {})
    )


@router.get("/stats", response_model=RouterStats)
async def get_router_stats(user: dict = Depends(get_current_user)):
    """Get ToolRouter statistics. Requires Admin role."""
    if "Admin" not in user.get("roles", []):
        audit_log("stats_access_denied", user, {})
        raise HTTPException(status_code=403, detail="Admin role required")
    
    tool_router = get_tool_router()
    stats = tool_router.get_stats()
    
    return RouterStats(
        total_agents=stats.get("total_agents", 0),
        total_tools=stats.get("total_tools", 0),
        avg_latency_seconds=stats.get("avg_latency_seconds", 0.0),
        recent_executions=stats.get("recent_executions", 0),
        error_count_recent=stats.get("error_count_recent", 0),
        agents=stats.get("agents", []),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
