"""
Agent Service Layer
Provides a unified facade for agent orchestration, registry access, and tool execution.
"""

import logging
from typing import Optional, Any
from twisterlab.agents.registry import get_agent_registry
from twisterlab.agents.base.adapter import AgentAdapter
from twisterlab.api.schemas.common import UnifiedAgentResponse, AgentErrorCode

logger = logging.getLogger(__name__)

class AgentService:
    """
    Service facade that simplifies agent interaction for API routes.
    Handles registry lookup, adapter wrapping, and standardized error mapping.
    """

    def __init__(self):
        self.registry = get_agent_registry()

    async def call_agent(self, agent_name: str, tool_name: str, **kwargs) -> UnifiedAgentResponse:
        """
        Highest-level entry point to call any agent tool.
        Abstracts registry, lazy loading, and normalization.
        """
        try:
            # 1. Fetch Wrapper
            adapter = self.get_wrapped_agent(agent_name)
            if not adapter:
                return UnifiedAgentResponse(
                    success=False,
                    error=f"Agent '{agent_name}' not found.",
                    error_code=AgentErrorCode.CAPABILITY_ERROR
                )

            # 2. Execute
            return await adapter.call(tool_name, **kwargs)

        except Exception as e:
            logger.exception(f"Unhandled error in AgentService for {agent_name}.{tool_name}")
            return UnifiedAgentResponse(
                success=False,
                error=str(e),
                error_code=AgentErrorCode.AGENT_FAILURE
            )

    def get_wrapped_agent(self, agent_name: str) -> Optional[AgentAdapter]:
        """
        Retrieves an agent from the registry and wraps it in an AgentAdapter.
        This provides the standardized execution boundary for services and Maestro.
        """
        agent_instance = self.registry.get_agent(agent_name)
        if not agent_instance:
            return None
        return AgentAdapter(agent_instance)

    def get_fleet_status(self) -> dict:
        """Returns the current registry diagnostics."""
        return self.registry.get_registry_status()

    def get_agent_metadata(self) -> dict:
        """Returns details for all registered agents."""
        return self.registry.list_agents()

# Global Service Singleton
_agent_service = None

def get_agent_service() -> AgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
