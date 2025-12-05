"""
TwisterLab Core Agents

This module contains MCP-agnostic agent implementations.
Agents define capabilities and logic without knowledge of MCP protocol.
"""

# Legacy import for backward compatibility
from .agent import Agent

# New unified architecture - Base classes
from .base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

# Concrete agents
from .monitoring import MonitoringAgent
from .maestro_agent import MaestroAgent
from .db_agent import DatabaseAgent
from .cache_agent import CacheAgent

__all__ = [
    # Legacy
    "Agent",
    # Base classes
    "TwisterAgent",
    "AgentCapability",
    "AgentResponse",
    "CapabilityType",
    "CapabilityParam",
    "ParamType",
    # Agents
    "MonitoringAgent",
    "MaestroAgent",
    "DatabaseAgent",
    "CacheAgent",
]
