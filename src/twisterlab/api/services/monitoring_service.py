import logging
from typing import Optional, Dict, Any, List
from twisterlab.api.schemas.common import UnifiedAgentResponse, AgentErrorCode
from twisterlab.api.services.agent_service import get_agent_service
from twisterlab.api.services.security_policy import SecurityPolicy

logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Specialized service for system health monitoring and metrics.
    Integrates centralized SecurityPolicy for safe external health checks.
    """

    def __init__(self):
        self.agent_service = get_agent_service()

    async def get_system_health(self, detailed: bool = False) -> UnifiedAgentResponse:
        """
        Collects comprehensive system health metrics from the Monitoring Agent.
        """
        logger.info(f"MonitoringService: Collecting health metrics (Detailed: {detailed})")
        
        try:
            return await self.agent_service.call_agent(
                "monitoring", 
                "monitor_system_health", 
                detailed=detailed
            )
        except Exception as e:
            logger.exception("MonitoringService: Metrics collection failed")
            return UnifiedAgentResponse(
                success=False,
                error=str(e),
                error_code=AgentErrorCode.AGENT_FAILURE
            )

    async def check_url_health(self, url: str) -> UnifiedAgentResponse:
        """
        Safely checks the health of a web endpoint with SSRF protection.
        """
        # 1. Centralized SSRF Pre-flight
        if not SecurityPolicy.validate_url(url):
            logger.warning(f"MonitoringService: Blocked SSRF attempt to '{url}'")
            return UnifiedAgentResponse(
                success=False,
                error="Security Policy: URL blocked (SSRF Protection).",
                error_code=AgentErrorCode.AUTH_ERROR
            )

        # 2. Call Browser for lightweight check
        try:
            return await self.agent_service.call_agent(
                "browser", 
                "browse", 
                url=url, 
                screenshot=False
            )
        except Exception as e:
            return UnifiedAgentResponse(
                success=False,
                error=f"Web health check failed: {str(e)}",
                error_code=AgentErrorCode.NETWORK_ERROR
            )

    def get_fleet_diagnostics(self) -> Dict[str, Any]:
        """
        Returns real-time status of the entire agent fleet.
        Redirects to the underlying registry stats.
        """
        return self.agent_service.get_fleet_status()

# Singleton provider
_monitoring_service = None

def get_monitoring_service() -> MonitoringService:
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
