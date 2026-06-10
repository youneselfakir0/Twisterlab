import logging
import httpx
from typing import Optional, Dict, Any, List
from twisterlab.api.schemas.common import UnifiedAgentResponse, AgentErrorCode
from twisterlab.api.services.agent_service import get_agent_service
from twisterlab.api.services.security_policy import SecurityPolicy
from opentelemetry import trace
from opentelemetry.trace import StatusCode

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
tracer = trace.get_tracer(__name__)

class OrchestrationService:
    """
    Master Service for complex multi-agent mission coordination.
    Handles safety pre-flights and standardized agent dispatch.
    """

    def __init__(self):
        self.agent_service = get_agent_service()

    async def _verify_webhook(self, url: str) -> bool:
        """
        Validates the n8n webhook before mission dispatch.
        Checks policy first, then performs a lightweight HEAD request.
        """
        if not url:
            return True # No webhook to verify

        # 1. SSRF/Safety Check
        if not SecurityPolicy.validate_url(url):
            logger.error(f"OrchestrationService: Blocked unsafe webhook '{url}'")
            return False

        # 2. Reachability Check (Pre-flight)
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # We use HEAD to minimize impact
                response = await client.head(url)
                # n8n webhooks usually return 200 even for raw GET, 
                # but any successful response means it's reachable.
                return response.status_code < 500
        except Exception as e:
            logger.warning(f"OrchestrationService: Webhook '{url}' reachability check failed: {e}")
            return False

    async def orchestrate_mission(self, task: str, context: Optional[Dict[str, Any]] = None) -> UnifiedAgentResponse:
        """
        Orchestrates a complete mission using Maestro.
        Includes pre-flight checks and service-aware agent wrapping.
        """
        context = context or {}
        webhook_url = context.get("webhook_url") or context.get("callback_url")
        
        logger.info(f"OrchestrationService: Starting mission for task '{task[:50]}'")

        # 1. Fail Fast: Webhook Verification
        if webhook_url:
            if not await self._verify_webhook(webhook_url):
                return UnifiedAgentResponse(
                    success=False,
                    error=f"Pre-flight failed: Webhook '{webhook_url}' is unreachable or blocked.",
                    error_code=AgentErrorCode.AUTH_ERROR
                )

        # 2. Prepare Maestro: Pass the Service-Aware Lookup
        dry_run = context.get("dry_run", False)
        
        def service_aware_lookup(agent_name: str):
            return self.agent_service.get_wrapped_agent(agent_name)

        # 3. Call Maestro with tracing
        with tracer.start_as_current_span(
            "maestro.orchestrate_mission",
            attributes={
                "task.length": len(task),
                "dry_run": dry_run,
                "has_webhook": bool(webhook_url)
            }
        ) as span:
            try:
                # 2. Prepare Maestro: Pass the Service-Aware Lookup
                dry_run = context.get("dry_run", False)
                
                def service_aware_lookup(agent_name: str):
                    return self.agent_service.get_wrapped_agent(agent_name)
                
                # 3. Call Maestro
                result = await self.agent_service.call_agent(
                    "maestro", 
                    "orchestrate", 
                    task=task,
                    context=context,
                    dry_run=dry_run,
                    lookup_fn=service_aware_lookup
                )
                
                # Add result attributes to span
                span.set_attribute("mission.success", result.success)
                if not result.success and result.error:
                    span.set_attribute("mission.error", result.error[:200])  # Truncate long errors
                
                span.set_status(StatusCode.OK)
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                logger.exception("OrchestrationService: Maestro failure")
                return UnifiedAgentResponse(
                    success=False,
                    error=str(e),
                    error_code=AgentErrorCode.AGENT_FAILURE
                )

# Singleton provider
_orchestration_service = None

def get_orchestration_service() -> OrchestrationService:
    global _orchestration_service
    if _orchestration_service is None:
        _orchestration_service = OrchestrationService()
    return _orchestration_service
