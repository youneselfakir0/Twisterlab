"""
Common schemas and enums for the TwisterLab API.
Provides unified types for tickets, agents, and error handling.
"""

from enum import Enum
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

class TicketCategory(str, Enum):
    """Unified ticket categories across classification and resolution."""
    NETWORK = "network"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    ACCOUNT = "account"
    EMAIL = "email"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATABASE = "database"
    GENERAL = "general"

class TicketPriority(str, Enum):
    """Unified ticket priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentErrorCode(str, Enum):
    """Standardized error codes for agent failures."""
    UNKNOWN = "UNKNOWN"
    AUTH_ERROR = "AUTH_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    CAPABILITY_ERROR = "CAPABILITY_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    AGENT_FAILURE = "AGENT_FAILURE"
    TIMEOUT = "TIMEOUT"

class UnifiedAgentResponse(BaseModel):
    """
    Standardized internal contract for all agent responses.
    This is used by the Service layer to interact with agents uniformly.
    """
    success: bool = Field(..., description="Whether the operation succeeded")
    data: Any = Field(None, description="The actual output of the agent if successful")
    error: Optional[str] = Field(None, description="Detailed error message if failed")
    error_code: Optional[AgentErrorCode] = Field(None, description="Standardized error code")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or execution metrics")

    class Config:
        use_enum_values = True

class MCPResponse(BaseModel):
    """
    Transport envelope for public API responses.
    Kept separate from internal AgentResponse for backward compatibility.
    """
    content: List[Dict[str, Any]] = Field(..., description="MCP-style content block")
    isError: bool = Field(False, description="Whether the request resulted in an error")
    status: str = Field("success", description="Legacy status string (success/error)")
    code: Optional[str] = Field(None, description="Stable machine-readable error code")
    trace_id: Optional[str] = Field(None, description="Correlation ID for server logs")
    debug: Optional[Dict[str, Any]] = Field(None, description="Diagnostic details (DEBUG=True only)")

    @classmethod
    def from_agent_response(cls, response: UnifiedAgentResponse) -> "MCPResponse":
        """Convert an internal agent response to a public MCP transport block."""
        import json
        
        # Format content block
        if response.success:
            if isinstance(response.data, (dict, list)):
                text = json.dumps(response.data, indent=2, default=str)
            else:
                text = str(response.data) if response.data else "OK"
            content = [{"type": "text", "text": text}]
        else:
            content = [{"type": "text", "text": f"Error: {response.error or 'Unknown failure'}"}]
            
        return cls(
            content=content,
            isError=not response.success,
            status="success" if response.success else "error"
        )
