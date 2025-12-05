"""
Agent Registry and Tool Router

Manages all agents and routes MCP tool calls to the correct agent.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from twisterlab.agents.core.base import TwisterAgent
from twisterlab.services import ServiceRegistry, get_service_registry
from .adapter import MCPAdapter

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for all TwisterLab agents.
    
    Manages agent lifecycle and provides discovery.
    """
    
    _instance: Optional[AgentRegistry] = None
    
    def __new__(cls) -> AgentRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._agents: Dict[str, TwisterAgent] = {}
        self._adapters: Dict[str, MCPAdapter] = {}
        self._service_registry: ServiceRegistry = get_service_registry()
        
        logger.info("AgentRegistry initialized")
    
    def register(
        self,
        agent_class: Type[TwisterAgent],
        name: str = None
    ) -> TwisterAgent:
        """
        Register an agent class.
        
        Args:
            agent_class: The TwisterAgent class to register
            name: Optional override for agent name
            
        Returns:
            The instantiated agent
        """
        agent = agent_class(self._service_registry)
        agent_name = name or agent.name
        
        self._agents[agent_name] = agent
        self._adapters[agent_name] = MCPAdapter(agent)
        
        logger.info(
            f"Registered agent: {agent_name} with "
            f"{len(agent.list_capabilities())} capabilities"
        )
        
        return agent
    
    def register_instance(self, agent: TwisterAgent) -> None:
        """Register an already-instantiated agent."""
        self._agents[agent.name] = agent
        self._adapters[agent.name] = MCPAdapter(agent)
        logger.info(f"Registered agent instance: {agent.name}")
    
    def get_agent(self, name: str) -> Optional[TwisterAgent]:
        """Get an agent by name."""
        return self._agents.get(name)
    
    def get_adapter(self, name: str) -> Optional[MCPAdapter]:
        """Get an adapter by agent name."""
        return self._adapters.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all agents with their info."""
        return [
            agent.to_dict()
            for agent in self._agents.values()
        ]


class ToolRouter:
    """
    Routes MCP tool calls to the correct agent.
    
    Handles:
    - Tool discovery across all agents
    - Tool execution routing
    - Response aggregation
    """
    
    def __init__(self, registry: AgentRegistry = None):
        self._registry = registry or AgentRegistry()
        self._tool_to_adapter: Dict[str, MCPAdapter] = {}
        self._rebuild_tool_map()
    
    def _rebuild_tool_map(self) -> None:
        """Rebuild mapping from tool names to adapters."""
        self._tool_to_adapter.clear()
        
        for agent_name in self._registry.list_agents():
            adapter = self._registry.get_adapter(agent_name)
            if adapter:
                for tool in adapter.list_tools():
                    self._tool_to_adapter[tool["name"]] = adapter
    
    def refresh(self) -> None:
        """Refresh tool mappings after agent changes."""
        self._rebuild_tool_map()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get all MCP tools from all agents.
        
        Returns:
            Combined list of all MCP tool definitions
        """
        tools = []
        
        for agent_name in self._registry.list_agents():
            adapter = self._registry.get_adapter(agent_name)
            if adapter:
                tools.extend(adapter.list_tools())
        
        return tools
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool definition."""
        adapter = self._tool_to_adapter.get(tool_name)
        if not adapter:
            return None
        
        for tool in adapter.list_tools():
            if tool["name"] == tool_name:
                return tool
        return None
    
    def can_handle(self, tool_name: str) -> bool:
        """Check if any agent can handle this tool."""
        return tool_name in self._tool_to_adapter
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool by routing to the correct agent.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            MCP content response
        """
        adapter = self._tool_to_adapter.get(tool_name)
        
        if not adapter:
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Unknown tool: {tool_name}"
                }]
            }
        
        return await adapter.execute_tool(tool_name, arguments)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "total_agents": len(self._registry.list_agents()),
            "total_tools": len(self._tool_to_adapter),
            "agents": [
                {
                    "name": name,
                    "tools": len(self._registry.get_adapter(name).list_tools())
                    if self._registry.get_adapter(name) else 0
                }
                for name in self._registry.list_agents()
            ]
        }


def get_agent_registry() -> AgentRegistry:
    """Get the singleton AgentRegistry instance."""
    return AgentRegistry()


def get_tool_router() -> ToolRouter:
    """Get a ToolRouter with the default registry."""
    return ToolRouter(get_agent_registry())
