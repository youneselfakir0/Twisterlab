"""
TwisterLab Agents Package.

This package contains all autonomous agents for the TwisterLab helpdesk automation system.
All agents follow the BaseAgent pattern and implement MCP isolation for security.

Lazy loading implementation to avoid database imports at startup.
"""

import logging
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)

# Lazy-loaded agents (avoid database imports at startup)
_LAZY_AGENTS: Dict[str, Type[Any]] = {}


def get_agent(name: str) -> Optional[Type[Any]]:
    """
    Lazy load agent to avoid database imports at startup.

    Args:
        name: Agent name (desktop_commander, ticket_classifier, resolver)

    Returns:
        Agent class or None if not available
    """
    if name not in _LAZY_AGENTS:
        try:
            if name == "desktop_commander":
                from agents.desktop_commander.desktop_commander_agent import DesktopCommanderAgent

                _LAZY_AGENTS[name] = DesktopCommanderAgent
            elif name == "ticket_classifier":
                from agents.helpdesk.classifier import TicketClassifierAgent

                _LAZY_AGENTS[name] = TicketClassifierAgent
            elif name == "resolver":
                from agents.resolver.resolver_agent import ResolverAgent

                _LAZY_AGENTS[name] = ResolverAgent
            else:
                logger.warning(f"Unknown agent: {name}")
                return None
        except ImportError as e:
            logger.warning(f"Agent {name} not available: {e}")
            return None

    return _LAZY_AGENTS[name]


# Core agents (safe to import - no database dependencies)
# Note: Core agents not yet implemented - using lazy loading for all agents
# from agents.core.backup_agent import BackupAgent
# from agents.core.maestro_orchestrator_agent import MaestroOrchestratorAgent
# from agents.core.monitoring_agent import MonitoringAgent
# from agents.core.sync_agent import SyncAgent

__all__ = [
    # "MaestroOrchestratorAgent",
    # "SyncAgent",
    # "BackupAgent",
    # "MonitoringAgent",
    "get_agent",  # Lazy loader for database-dependent agents
]
