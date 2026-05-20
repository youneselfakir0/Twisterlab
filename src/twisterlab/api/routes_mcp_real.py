"""
TwisterLab MCP API Routes - Real Agent Endpoints
Modernized Service-Oriented Routes (Phase 2)
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Imports Core
from twisterlab.agents.core.database import get_db_session
from twisterlab.api.services.agent_service import get_agent_service, AgentService
from twisterlab.api.services.classification_service import get_classification_service, ClassificationService
from twisterlab.api.services.resolution_service import get_resolution_service, ResolutionService
from twisterlab.api.services.monitoring_service import get_monitoring_service, MonitoringService
from twisterlab.api.services.orchestration_service import get_orchestration_service, OrchestrationService
from twisterlab.api.schemas.common import MCPResponse, UnifiedAgentResponse, AgentErrorCode

# Pydantic Models
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(tags=["mcp-tools"])

# ============================================================================
# REQUEST MODELS
# ============================================================================

class ClassifyTicketRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=5000)

class ResolveTicketRequest(BaseModel):
    category: str = Field(...)
    ticket_id: Optional[int] = Field(None)
    description: Optional[str] = Field(None)

class MonitorSystemHealthRequest(BaseModel):
    detailed: bool = Field(False)

class OrchestrateRequest(BaseModel):
    task: str = Field(..., min_length=5)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    dry_run: bool = Field(False)

class BrowseWebRequest(BaseModel):
    url: str = Field(..., description="URL to visit")
    screenshot: bool = Field(True)

class AnalyzeCodeRequest(BaseModel):
    code: str = Field(...)
    language: str = Field("python")

# ============================================================================
# DISCOVERY & REGISTRY
# ============================================================================

@router.get("/list_autonomous_agents", response_model=MCPResponse)
@router.post("/list_autonomous_agents", response_model=MCPResponse)
async def list_autonomous_agents(
    service: AgentService = Depends(get_agent_service)
) -> MCPResponse:
    """List all agents using live registry metadata."""
    try:
        metadata = service.get_agent_metadata()
        status_info = service.get_fleet_status()
        
        agents_list = [{"id": k, **v} for k, v in metadata.items()]
        
        data = {
            "version": "3.8.2-modern",
            "total": status_info["total_registered"],
            "agents": agents_list,
            "status": status_info["status_breakdown"]
        }
        return MCPResponse.from_agent_response(UnifiedAgentResponse(success=True, data=data))
    except Exception as e:
        return MCPResponse.from_agent_response(UnifiedAgentResponse(success=False, error=str(e)))

@router.get("/health")
async def mcp_health(service: MonitoringService = Depends(get_monitoring_service)):
    """Dynamic health check via MonitoringService."""
    res = await service.get_system_health(detailed=True)
    fleet = service.get_fleet_diagnostics()
    
    return {
        "status": "ok" if res.success else "degraded",
        "system": res.data if res.success else {"error": res.error},
        "fleet": fleet
    }

# ============================================================================
# CORE TOOLS (Classification, Resolution, Monitoring)
# ============================================================================

@router.post("/classify_ticket", response_model=MCPResponse)
@router.post("/twisterlab_mcp_classify_ticket", response_model=MCPResponse)
async def classify_ticket(
    request: ClassifyTicketRequest,
    service: ClassificationService = Depends(get_classification_service)
) -> MCPResponse:
    """Classify ticket via specialized ClassificationService."""
    res = await service.classify_ticket(request.description)
    return MCPResponse.from_agent_response(res)

@router.post("/resolve_ticket", response_model=MCPResponse)
@router.post("/twisterlab_mcp_resolve_ticket", response_model=MCPResponse)
async def resolve_ticket(
    request: ResolveTicketRequest,
    session: AsyncSession = Depends(get_db_session),
    service: ResolutionService = Depends(get_resolution_service)
) -> MCPResponse:
    """Resolve ticket via specialized ResolutionService."""
    res = await service.resolve_ticket(
        category=request.category,
        ticket_id=request.ticket_id,
        description=request.description,
        session=session
    )
    return MCPResponse.from_agent_response(res)

@router.post("/monitor_system_health", response_model=MCPResponse)
async def monitor_system_health(
    request: MonitorSystemHealthRequest,
    service: MonitoringService = Depends(get_monitoring_service)
) -> MCPResponse:
    """Monitor health via MonitoringService."""
    res = await service.get_system_health(detailed=request.detailed)
    return MCPResponse.from_agent_response(res)

# ============================================================================
# ORCHESTRATION TOOL (Maestro)
# ============================================================================

@router.post("/orchestrate", response_model=MCPResponse)
@router.post("/maestro_orchestrate", response_model=MCPResponse)
@router.post("/twisterlab_mcp_orchestrate", response_model=MCPResponse)
async def orchestrate(
    request: OrchestrateRequest,
    service: OrchestrationService = Depends(get_orchestration_service)
) -> MCPResponse:
    """Orchestrate mission via specialized OrchestrationService (includes safety pre-flights)."""
    res = await service.orchestrate_mission(request.task, request.context)
    return MCPResponse.from_agent_response(res)

# ============================================================================
# UTILITY TOOLS (Browser, Code, Commander)
# ============================================================================

@router.post("/browse_web", response_model=MCPResponse)
async def browse_web(
    request: BrowseWebRequest,
    service: MonitoringService = Depends(get_monitoring_service)
) -> MCPResponse:
    """Check web health via MonitoringService (safely validates SSRF)."""
    res = await service.check_url_health(request.url)
    return MCPResponse.from_agent_response(res)

@router.post("/analyze_code", response_model=MCPResponse)
async def analyze_code(
    request: AnalyzeCodeRequest,
    service: AgentService = Depends(get_agent_service)
) -> MCPResponse:
    """Analyze code via Generic AgentService."""
    res = await service.call_agent("code-review", "analyze_code", code=request.code, language=request.language)
    return MCPResponse.from_agent_response(res)

@router.post("/execute_command", response_model=MCPResponse)
async def execute_command(
    command: str,
    service: AgentService = Depends(get_agent_service)
) -> MCPResponse:
    """Execute command via Generic AgentService."""
    res = await service.call_agent("commander", "execute_command", command=command)
    return MCPResponse.from_agent_response(res)
