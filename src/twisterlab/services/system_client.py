"""
Docker/System Client

Concrete implementation of SystemClient for Docker and system monitoring.
Uses Docker SDK for container management.
"""

from __future__ import annotations

import logging
import platform
import time
from typing import Any, Dict, List, Optional

from .base import (
    ContainerInfo,
    ContainerState,
    ServiceHealth,
    ServiceInfo,
    ServiceStatus,
    SystemClient,
    SystemMetrics,
)

logger = logging.getLogger(__name__)

# Try to import docker
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("docker SDK not available - system client will use fallback mode")

# Try to import psutil for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - limited system metrics")


class DockerSystemClient(SystemClient):
    """
    System client for Docker and OS metrics.
    
    Provides container management and system monitoring.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        self._base_url = base_url
        self._client: Optional["docker.DockerClient"] = None
        logger.info("DockerSystemClient initialized")
    
    @property
    def name(self) -> str:
        return "docker"
    
    def _get_client(self) -> "docker.DockerClient":
        """Get or create Docker client."""
        if self._client is None:
            if not DOCKER_AVAILABLE:
                raise RuntimeError("docker SDK not available")
            if self._base_url:
                self._client = docker.DockerClient(base_url=self._base_url)
            else:
                self._client = docker.from_env()
        return self._client
    
    async def list_containers(
        self,
        all_containers: bool = False
    ) -> List[ContainerInfo]:
        """List Docker containers."""
        if not DOCKER_AVAILABLE:
            return []
        
        try:
            client = self._get_client()
            containers = client.containers.list(all=all_containers)
            
            result = []
            for c in containers:
                # Determine state
                status = c.status.lower()
                if status == "running":
                    state = ContainerState.RUNNING
                elif status == "exited":
                    state = ContainerState.STOPPED
                elif status == "paused":
                    state = ContainerState.PAUSED
                elif status in ("restarting", "created"):
                    state = ContainerState.STARTING
                else:
                    state = ContainerState.UNKNOWN
                
                # Get image name
                image_name = c.image.tags[0] if c.image.tags else c.image.short_id
                
                # Get port mappings
                ports = {}
                for port, bindings in (c.ports or {}).items():
                    if bindings:
                        host_port = bindings[0].get("HostPort")
                        if host_port:
                            ports[port] = int(host_port)
                
                result.append(ContainerInfo(
                    id=c.short_id,
                    name=c.name,
                    image=image_name,
                    state=state,
                    created=c.attrs.get("Created", ""),
                    ports=ports,
                    labels=c.labels or {},
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Docker list_containers error: {e}")
            return []
    
    async def get_container(self, container_id: str) -> Optional[ContainerInfo]:
        """Get a specific container by ID or name."""
        if not DOCKER_AVAILABLE:
            return None
        
        try:
            client = self._get_client()
            c = client.containers.get(container_id)
            
            status = c.status.lower()
            state = {
                "running": ContainerState.RUNNING,
                "exited": ContainerState.STOPPED,
                "paused": ContainerState.PAUSED,
            }.get(status, ContainerState.UNKNOWN)
            
            return ContainerInfo(
                id=c.short_id,
                name=c.name,
                image=c.image.tags[0] if c.image.tags else c.image.short_id,
                state=state,
                created=c.attrs.get("Created", ""),
                ports={},
                labels=c.labels or {},
            )
            
        except Exception as e:
            logger.error(f"Docker get_container error: {e}")
            return None
    
    async def container_logs(
        self,
        container_id: str,
        tail: int = 100
    ) -> str:
        """Get container logs."""
        if not DOCKER_AVAILABLE:
            return ""
        
        try:
            client = self._get_client()
            container = client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode("utf-8", errors="replace")
            
        except Exception as e:
            logger.error(f"Docker container_logs error: {e}")
            return f"Error: {e}"
    
    async def list_services(self) -> List[ServiceInfo]:
        """List Docker Swarm services (or running containers as services)."""
        if not DOCKER_AVAILABLE:
            return []
        
        try:
            client = self._get_client()
            
            # Try Swarm services first
            try:
                services = client.services.list()
                return [
                    ServiceInfo(
                        name=s.name,
                        status="active",
                        replicas=s.attrs.get("Spec", {}).get("Mode", {}).get("Replicated", {}).get("Replicas", 1),
                    )
                    for s in services
                ]
            except Exception:
                # Fallback to containers as services
                containers = client.containers.list()
                return [
                    ServiceInfo(
                        name=c.name,
                        status="running" if c.status == "running" else "stopped",
                        replicas=1,
                    )
                    for c in containers
                ]
                
        except Exception as e:
            logger.error(f"Docker list_services error: {e}")
            return []
    
    async def get_metrics(self) -> SystemMetrics:
        """Get system metrics (CPU, memory, disk)."""
        try:
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                
                # Count containers if Docker is available
                container_count = 0
                if DOCKER_AVAILABLE:
                    try:
                        client = self._get_client()
                        container_count = len(client.containers.list())
                    except Exception:
                        pass
                
                return SystemMetrics(
                    cpu_percent=cpu,
                    memory_percent=mem.percent,
                    memory_used_gb=round(mem.used / (1024**3), 2),
                    memory_total_gb=round(mem.total / (1024**3), 2),
                    disk_percent=disk.percent,
                    disk_used_gb=round(disk.used / (1024**3), 2),
                    disk_total_gb=round(disk.total / (1024**3), 2),
                    container_count=container_count,
                )
            else:
                # Fallback metrics
                return SystemMetrics(
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    memory_used_gb=0.0,
                    memory_total_gb=0.0,
                    disk_percent=0.0,
                    disk_used_gb=0.0,
                    disk_total_gb=0.0,
                    container_count=0,
                )
                
        except Exception as e:
            logger.error(f"System metrics error: {e}")
            return SystemMetrics()
    
    async def health_check(self) -> ServiceHealth:
        """Check Docker daemon health."""
        if not DOCKER_AVAILABLE:
            return ServiceHealth(
                name=self.name,
                status=ServiceStatus.DEGRADED,
                message="docker SDK not available"
            )
        
        try:
            start = time.perf_counter()
            client = self._get_client()
            info = client.info()
            elapsed = (time.perf_counter() - start) * 1000
            
            return ServiceHealth(
                name=self.name,
                status=ServiceStatus.CONNECTED,
                latency_ms=elapsed,
                message="OK",
                metadata={
                    "containers_running": info.get("ContainersRunning", 0),
                    "containers_stopped": info.get("ContainersStopped", 0),
                    "images": info.get("Images", 0),
                    "server_version": info.get("ServerVersion"),
                    "os": info.get("OperatingSystem"),
                }
            )
            
        except Exception as e:
            return ServiceHealth(
                name=self.name,
                status=ServiceStatus.DISCONNECTED,
                message=str(e)
            )
    
    async def close(self) -> None:
        """Close Docker client."""
        if self._client:
            self._client.close()
            self._client = None
    
    # Additional utility methods
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        info = {
            "hostname": platform.node(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }
        
        if PSUTIL_AVAILABLE:
            info.update({
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "boot_time": psutil.boot_time(),
            })
        
        if DOCKER_AVAILABLE:
            try:
                client = self._get_client()
                docker_info = client.info()
                info["docker"] = {
                    "version": docker_info.get("ServerVersion"),
                    "containers": docker_info.get("Containers", 0),
                    "images": docker_info.get("Images", 0),
                    "driver": docker_info.get("Driver"),
                }
            except Exception:
                info["docker"] = None
        
        return info
