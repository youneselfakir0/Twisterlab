"""
MCP Adapter Module

This module provides the MCP protocol adapter layer that converts
MCP-agnostic agents into MCP-compatible servers.

Architecture:
    TwisterAgent (MCP-agnostic) → MCPAdapter → MCP Protocol

Components:
    - MCPAdapter: Converts agent capabilities to MCP tools
    - UnifiedMCPServer: Single MCP server exposing all agents
    - ToolRouter: Routes MCP tool calls to correct agent
"""

from .adapter import MCPAdapter
from .server import UnifiedMCPServer
from .router import ToolRouter, AgentRegistry

__all__ = [
    "MCPAdapter",
    "UnifiedMCPServer",
    "ToolRouter",
    "AgentRegistry",
]
