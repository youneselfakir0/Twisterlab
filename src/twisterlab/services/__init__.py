"""
TwisterLab Services Layer

This module provides the service interfaces (ports) and concrete implementations
(adapters) for external service connections:

- LLMClient → CortexClient (Ollama/Cortex LLM)
- CacheClient → RedisServiceClient (Redis)
- DBClient → PostgresClient (PostgreSQL)
- SystemClient → DockerSystemClient (Docker + System metrics)

Usage:
    from twisterlab.services import ServiceRegistry, get_service_registry

    registry = get_service_registry()
    llm = registry.get_llm()
    cache = registry.get_cache()
    db = registry.get_db()
    system = registry.get_system()
"""

from .base import (
    # Abstract interfaces
    LLMClient,
    CacheClient,
    DBClient,
    SystemClient,
    # Data classes
    LLMResponse,
    CacheStats,
    QueryResult,
    ContainerInfo,
    ContainerState,
    ServiceInfo,
    SystemMetrics,
    ServiceHealth,
    ServiceStatus,
)

from .registry import ServiceRegistry, get_service_registry

from .cortex import CortexClient
from .redis_client import RedisServiceClient
from .postgres_client import PostgresClient
from .system_client import DockerSystemClient

__all__ = [
    # Registry
    "ServiceRegistry",
    "get_service_registry",
    # Abstract interfaces
    "LLMClient",
    "CacheClient",
    "DBClient",
    "SystemClient",
    # Concrete implementations
    "CortexClient",
    "RedisServiceClient",
    "PostgresClient",
    "DockerSystemClient",
    # Data classes
    "LLMResponse",
    "CacheStats",
    "QueryResult",
    "ContainerInfo",
    "ContainerState",
    "ServiceInfo",
    "SystemMetrics",
    "ServiceHealth",
    "ServiceStatus",
]
