"""
TwisterAgent Base Class

This is the foundation for all MCP-agnostic agents in TwisterLab.
Agents are pure Python classes that:
- Define capabilities (tools) with metadata
- Implement business logic
- Have NO knowledge of MCP protocol

The MCP adapter layer handles protocol translation.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from twisterlab.services import ServiceRegistry, get_service_registry

logger = logging.getLogger(__name__)


class CapabilityType(str, Enum):
    """Types of agent capabilities."""

    QUERY = "query"  # Read-only operation
    ACTION = "action"  # State-changing operation
    STREAM = "stream"  # Streaming response


class ParamType(str, Enum):
    """Parameter types for capability inputs."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class CapabilityParam:
    """Definition of a capability parameter."""

    name: str
    param_type: ParamType
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class AgentCapability:
    """
    Definition of an agent capability (tool).

    This is the agent's declaration of what it can do.
    The MCP adapter converts this to MCP tool schemas.
    """

    name: str
    description: str
    handler: str  # Method name on the agent
    capability_type: CapabilityType = CapabilityType.QUERY
    params: List[CapabilityParam] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema for MCP tools."""
        properties = {}
        required = []

        for param in self.params:
            prop = {
                "type": param.param_type.value,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop

            if param.required and param.default is None:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }


@dataclass
class AgentResponse:
    """
    Standardized response from agent operations.

    All agent methods should return this for consistent handling.
    """

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_mcp_content(self) -> List[Dict[str, Any]]:
        """Convert to MCP content format."""
        if self.success:
            import json

            if isinstance(self.data, (dict, list)):
                text = json.dumps(self.data, indent=2, default=str)
            else:
                text = str(self.data) if self.data else "OK"
            return [{"type": "text", "text": text}]
        else:
            return [{"type": "text", "text": f"Error: {self.error}"}]


class CoreAgent(ABC):
    """
    Base class for all TwisterLab Core System Agents.

    Agents are MCP-agnostic - they define capabilities and implement
    business logic without any knowledge of MCP protocol.

    Example:
        class MyAgent(CoreAgent):
            @property
            def name(self) -> str:
                return "my_agent"

            @property
            def description(self) -> str:
                return "My custom agent"

            def get_capabilities(self) -> List[AgentCapability]:
                return [
                    AgentCapability(
                        name="do_something",
                        description="Does something useful",
                        handler="handle_do_something",
                        params=[
                            CapabilityParam("input", ParamType.STRING, "Input value")
                        ]
                    )
                ]

            async def handle_do_something(self, input: str) -> AgentResponse:
                return AgentResponse(success=True, data=f"Did: {input}")
    """

    def __init__(self, registry: Optional[ServiceRegistry] = None):
        """Initialize with optional service registry."""
        self._registry = registry or get_service_registry()
        self._capabilities: Optional[List[AgentCapability]] = None
        logger.info(f"Agent initialized: {self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this agent."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this agent."""
        pass

    @property
    def version(self) -> str:
        """Agent version."""
        return "1.0.0"

    @property
    def registry(self) -> ServiceRegistry:
        """Get the service registry."""
        return self._registry

    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """
        Return list of capabilities this agent provides.

        Override this to define what the agent can do.
        """
        pass

    def list_capabilities(self) -> List[AgentCapability]:
        """Get cached list of capabilities."""
        if self._capabilities is None:
            self._capabilities = self.get_capabilities()
        return self._capabilities

    def get_capability(self, name: str) -> Optional[AgentCapability]:
        """Get a specific capability by name."""
        for cap in self.list_capabilities():
            if cap.name == name:
                return cap
        return None

    async def execute(self, capability_name: str, **kwargs) -> AgentResponse:
        """
        Execute a capability by name.

        This is the main entry point for running agent operations.
        It looks up the capability and calls the handler method.
        """
        capability = self.get_capability(capability_name)
        if not capability:
            return AgentResponse(
                success=False, error=f"Unknown capability: {capability_name}"
            )

        # Get handler method
        handler = getattr(self, capability.handler, None)
        if not handler:
            return AgentResponse(
                success=False, error=f"Handler not found: {capability.handler}"
            )

        try:
            # Call handler with kwargs
            result = await handler(**kwargs)

            # Ensure result is AgentResponse
            if isinstance(result, AgentResponse):
                return result
            else:
                return AgentResponse(success=True, data=result)

        except Exception as e:
            logger.exception(f"Error executing {capability_name}")
            return AgentResponse(success=False, error=str(e))

    async def health_check(self) -> AgentResponse:
        """Check agent health."""
        return AgentResponse(
            success=True,
            data={
                "agent": self.name,
                "version": self.version,
                "capabilities": len(self.list_capabilities()),
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent info to dict."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "type": c.capability_type.value,
                    "params": c.to_json_schema(),
                    "tags": c.tags,
                }
                for c in self.list_capabilities()
            ],
        }

# Deprecated alias for backward compatibility
TwisterAgent = CoreAgent
