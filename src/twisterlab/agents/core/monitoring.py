"""
Monitoring Agent

MCP-agnostic agent for system and infrastructure monitoring.
Provides capabilities for checking services, containers, and metrics.
"""

from __future__ import annotations

import logging
from typing import List

from .base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


class MonitoringAgent(TwisterAgent):
    """
    Agent for monitoring TwisterLab infrastructure.
    
    Provides capabilities for:
    - Service health checks
    - Container monitoring
    - System metrics
    - Log viewing
    """
    
    @property
    def name(self) -> str:
        return "monitoring"
    
    @property
    def description(self) -> str:
        return "Infrastructure monitoring and health checks"
    
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            # Health & Status
            AgentCapability(
                name="health_check",
                description="Check health of all TwisterLab services",
                handler="handle_health_check",
                capability_type=CapabilityType.QUERY,
                tags=["health", "status"],
            ),
            AgentCapability(
                name="get_system_metrics",
                description="Get system metrics (CPU, memory, disk)",
                handler="handle_get_system_metrics",
                capability_type=CapabilityType.QUERY,
                tags=["metrics", "system"],
            ),
            
            # Containers
            AgentCapability(
                name="list_containers",
                description="List all Docker containers",
                handler="handle_list_containers",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "all",
                        ParamType.BOOLEAN,
                        "Include stopped containers",
                        required=False,
                        default=False,
                    )
                ],
                tags=["docker", "containers"],
            ),
            AgentCapability(
                name="get_container_logs",
                description="Get logs from a Docker container",
                handler="handle_get_container_logs",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "container_id",
                        ParamType.STRING,
                        "Container ID or name",
                    ),
                    CapabilityParam(
                        "tail",
                        ParamType.INTEGER,
                        "Number of lines to return",
                        required=False,
                        default=100,
                    ),
                ],
                tags=["docker", "logs"],
            ),
            
            # Cache
            AgentCapability(
                name="get_cache_stats",
                description="Get Redis cache statistics",
                handler="handle_get_cache_stats",
                capability_type=CapabilityType.QUERY,
                tags=["cache", "redis"],
            ),
            
            # LLM
            AgentCapability(
                name="get_llm_status",
                description="Check Cortex LLM server status",
                handler="handle_get_llm_status",
                capability_type=CapabilityType.QUERY,
                tags=["llm", "cortex"],
            ),
            AgentCapability(
                name="list_models",
                description="List available LLM models",
                handler="handle_list_models",
                capability_type=CapabilityType.QUERY,
                tags=["llm", "models"],
            ),
        ]
    
    # =========================================================================
    # Handler Methods
    # =========================================================================
    
    async def handle_health_check(self) -> AgentResponse:
        """Check health of all services."""
        try:
            health = await self.registry.health_check_all()
            
            # Convert to serializable format
            results = {}
            for name, h in health.items():
                results[name] = {
                    "status": h.status.value,
                    "latency_ms": h.latency_ms,
                    "message": h.message,
                    "metadata": h.metadata,
                }
            
            # Determine overall status
            all_connected = all(
                h.status.value == "connected"
                for h in health.values()
            )
            
            return AgentResponse(
                success=True,
                data={
                    "overall": "healthy" if all_connected else "degraded",
                    "services": results,
                }
            )
        except Exception as e:
            logger.exception("Health check failed")
            return AgentResponse(success=False, error=str(e))
    
    async def handle_get_system_metrics(self) -> AgentResponse:
        """Get system metrics."""
        try:
            system = self.registry.get_system()
            metrics = await system.get_metrics()
            
            return AgentResponse(
                success=True,
                data={
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "memory_used_gb": metrics.memory_used_gb,
                    "memory_total_gb": metrics.memory_total_gb,
                    "disk_percent": metrics.disk_percent,
                    "disk_used_gb": metrics.disk_used_gb,
                    "disk_total_gb": metrics.disk_total_gb,
                    "container_count": metrics.container_count,
                }
            )
        except Exception as e:
            logger.exception("Failed to get system metrics")
            return AgentResponse(success=False, error=str(e))
    
    async def handle_list_containers(
        self,
        all: bool = False
    ) -> AgentResponse:
        """List Docker containers."""
        try:
            system = self.registry.get_system()
            containers = await system.list_containers(all_containers=all)
            
            return AgentResponse(
                success=True,
                data=[
                    {
                        "id": c.id,
                        "name": c.name,
                        "image": c.image,
                        "state": c.state.value,
                        "ports": c.ports,
                    }
                    for c in containers
                ]
            )
        except Exception as e:
            logger.exception("Failed to list containers")
            return AgentResponse(success=False, error=str(e))
    
    async def handle_get_container_logs(
        self,
        container_id: str,
        tail: int = 100
    ) -> AgentResponse:
        """Get container logs."""
        try:
            system = self.registry.get_system()
            logs = await system.container_logs(container_id, tail=tail)
            
            return AgentResponse(
                success=True,
                data={
                    "container": container_id,
                    "lines": tail,
                    "logs": logs,
                }
            )
        except Exception as e:
            logger.exception(f"Failed to get logs for {container_id}")
            return AgentResponse(success=False, error=str(e))
    
    async def handle_get_cache_stats(self) -> AgentResponse:
        """Get Redis cache statistics."""
        try:
            cache = self.registry.get_cache()
            stats = await cache.get_stats()
            
            return AgentResponse(
                success=True,
                data={
                    "connected_clients": stats.connected_clients,
                    "used_memory": stats.used_memory,
                    "total_keys": stats.total_keys,
                    "hits": stats.hits,
                    "misses": stats.misses,
                    "hit_rate": f"{stats.hit_rate:.1f}%",
                }
            )
        except Exception as e:
            logger.exception("Failed to get cache stats")
            return AgentResponse(success=False, error=str(e))
    
    async def handle_get_llm_status(self) -> AgentResponse:
        """Check LLM server status."""
        try:
            llm = self.registry.get_llm()
            health = await llm.health_check()
            
            return AgentResponse(
                success=True,
                data={
                    "name": health.name,
                    "status": health.status.value,
                    "latency_ms": health.latency_ms,
                    "message": health.message,
                    "metadata": health.metadata,
                }
            )
        except Exception as e:
            logger.exception("Failed to check LLM status")
            return AgentResponse(success=False, error=str(e))
    
    async def handle_list_models(self) -> AgentResponse:
        """List available LLM models."""
        try:
            llm = self.registry.get_llm()
            models = await llm.list_models()
            
            return AgentResponse(
                success=True,
                data={
                    "models": models,
                    "count": len(models),
                }
            )
        except Exception as e:
            logger.exception("Failed to list models")
            return AgentResponse(success=False, error=str(e))
