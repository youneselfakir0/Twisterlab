"""
MCP Adapter

Converts MCP-agnostic TwisterAgent capabilities to MCP tool schemas.
This is the bridge between agent logic and MCP protocol.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    ParamType,
)

logger = logging.getLogger(__name__)


class MCPAdapter:
    """
    Adapter that converts TwisterAgent capabilities to MCP tools.
    
    This class:
    1. Takes an MCP-agnostic agent
    2. Converts its capabilities to MCP tool schemas
    3. Handles tool invocation and response formatting
    
    Example:
        agent = MonitoringAgent()
        adapter = MCPAdapter(agent)
        
        # Get MCP tools
        tools = adapter.list_tools()
        
        # Execute a tool
        result = await adapter.execute_tool("health_check", {})
    """
    
    # Map ParamType to JSON Schema types
    TYPE_MAP = {
        ParamType.STRING: "string",
        ParamType.INTEGER: "integer",
        ParamType.NUMBER: "number",
        ParamType.BOOLEAN: "boolean",
        ParamType.ARRAY: "array",
        ParamType.OBJECT: "object",
    }
    
    def __init__(self, agent: TwisterAgent, prefix: str = None):
        """
        Initialize adapter for an agent.
        
        Args:
            agent: The TwisterAgent to adapt
            prefix: Optional prefix for tool names (e.g., "monitoring_")
        """
        self.agent = agent
        self.prefix = prefix or f"{agent.name}_"
        self._tool_map: Dict[str, AgentCapability] = {}
        self._build_tool_map()
    
    def _build_tool_map(self) -> None:
        """Build mapping from tool names to capabilities."""
        for capability in self.agent.list_capabilities():
            tool_name = f"{self.prefix}{capability.name}"
            self._tool_map[tool_name] = capability
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get MCP tool schemas for all agent capabilities.
        
        Returns:
            List of MCP tool definitions
        """
        tools = []
        
        for capability in self.agent.list_capabilities():
            tool_name = f"{self.prefix}{capability.name}"
            
            # Build input schema
            properties = {}
            required = []
            
            for param in capability.params:
                prop = {
                    "type": self.TYPE_MAP.get(param.param_type, "string"),
                    "description": param.description,
                }
                
                if param.enum:
                    prop["enum"] = param.enum
                if param.default is not None:
                    prop["default"] = param.default
                
                properties[param.name] = prop
                
                if param.required and param.default is None:
                    required.append(param.name)
            
            tools.append({
                "name": tool_name,
                "description": capability.description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            })
        
        return tools
    
    def get_capability(self, tool_name: str) -> AgentCapability | None:
        """Get capability for a tool name."""
        return self._tool_map.get(tool_name)
    
    def can_handle(self, tool_name: str) -> bool:
        """Check if this adapter handles the given tool."""
        return tool_name in self._tool_map
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool and return MCP-formatted response.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            MCP content response
        """
        capability = self._tool_map.get(tool_name)
        if not capability:
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Unknown tool: {tool_name}"
                }]
            }
        
        try:
            # Execute via agent
            result = await self.agent.execute(capability.name, **arguments)
            
            # Convert to MCP content
            return {
                "isError": not result.success,
                "content": result.to_mcp_content()
            }
            
        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }]
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information for MCP."""
        return {
            "name": self.agent.name,
            "description": self.agent.description,
            "version": self.agent.version,
            "tool_count": len(self._tool_map),
        }
