"""
Service Registry for TwisterLab

Centralizes access to all external services with lazy initialization
and health monitoring.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional, Type, TypeVar

from .base import (
    LLMClient,
    CacheClient,
    DBClient,
    SystemClient,
    ServiceHealth,
    ServiceStatus,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceRegistry:
    """
    Singleton registry for all external services.
    
    Provides:
    - Lazy initialization of service clients
    - Centralized configuration
    - Health monitoring across all services
    - Easy swapping of implementations
    
    Usage:
        registry = get_service_registry()
        llm = registry.get_llm()
        cache = registry.get_cache()
    """
    
    _instance: Optional[ServiceRegistry] = None
    
    def __new__(cls) -> ServiceRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        # Service instances (lazy loaded)
        self._llm: Optional[LLMClient] = None
        self._cache: Optional[CacheClient] = None
        self._db: Optional[DBClient] = None
        self._system: Optional[SystemClient] = None
        
        # Configuration from environment
        self._config = {
            "cortex_url": os.getenv("CORTEX_ENDPOINT", "http://192.168.0.20:11434"),
            "redis_url": os.getenv("REDIS_URL", "redis://192.168.0.30:6379"),
            "postgres_url": os.getenv("DATABASE_URL", "postgresql://twisterlab:twisterlab@192.168.0.30:5432/twisterlab"),
            "edgeserver_url": os.getenv("EDGESERVER_ENDPOINT", "http://192.168.0.30:8000"),
        }
        
        logger.info("ServiceRegistry initialized")
    
    # =========================================================================
    # Service Getters (Lazy Initialization)
    # =========================================================================
    
    def get_llm(self) -> LLMClient:
        """Get LLM client (Cortex/Ollama)."""
        if self._llm is None:
            from .cortex import CortexClient
            self._llm = CortexClient(self._config["cortex_url"])
            logger.info(f"LLM client initialized: {self._llm.name}")
        return self._llm
    
    def get_cache(self) -> CacheClient:
        """Get cache client (Redis)."""
        if self._cache is None:
            from .redis_client import RedisServiceClient
            self._cache = RedisServiceClient(self._config["redis_url"])
            logger.info(f"Cache client initialized: {self._cache.name}")
        return self._cache
    
    def get_db(self) -> DBClient:
        """Get database client (PostgreSQL)."""
        if self._db is None:
            from .postgres_client import PostgresClient
            self._db = PostgresClient(self._config["postgres_url"])
            logger.info(f"DB client initialized: {self._db.name}")
        return self._db
    
    def get_system(self) -> SystemClient:
        """Get system client (Docker/SSH)."""
        if self._system is None:
            from .system_client import DockerSystemClient
            self._system = DockerSystemClient()
            logger.info(f"System client initialized: {self._system.name}")
        return self._system
    
    # =========================================================================
    # Injection / Override (for testing)
    # =========================================================================
    
    def set_llm(self, client: LLMClient) -> None:
        """Override LLM client (for testing)."""
        self._llm = client
    
    def set_cache(self, client: CacheClient) -> None:
        """Override cache client (for testing)."""
        self._cache = client
    
    def set_db(self, client: DBClient) -> None:
        """Override DB client (for testing)."""
        self._db = client
    
    def set_system(self, client: SystemClient) -> None:
        """Override system client (for testing)."""
        self._system = client
    
    # =========================================================================
    # Health Monitoring
    # =========================================================================
    
    async def health_check_all(self) -> Dict[str, ServiceHealth]:
        """Check health of all initialized services."""
        results = {}
        
        if self._llm is not None:
            try:
                results["llm"] = await self._llm.health_check()
            except Exception as e:
                results["llm"] = ServiceHealth(
                    name="llm",
                    status=ServiceStatus.DISCONNECTED,
                    message=str(e)
                )
        
        if self._cache is not None:
            try:
                results["cache"] = await self._cache.health_check()
            except Exception as e:
                results["cache"] = ServiceHealth(
                    name="cache",
                    status=ServiceStatus.DISCONNECTED,
                    message=str(e)
                )
        
        if self._db is not None:
            try:
                results["db"] = await self._db.health_check()
            except Exception as e:
                results["db"] = ServiceHealth(
                    name="db",
                    status=ServiceStatus.DISCONNECTED,
                    message=str(e)
                )
        
        if self._system is not None:
            try:
                results["system"] = await self._system.health_check()
            except Exception as e:
                results["system"] = ServiceHealth(
                    name="system",
                    status=ServiceStatus.DISCONNECTED,
                    message=str(e)
                )
        
        return results
    
    def get_config(self) -> Dict[str, str]:
        """Get current configuration."""
        return self._config.copy()
    
    def update_config(self, **kwargs) -> None:
        """Update configuration."""
        self._config.update(kwargs)
        # Reset clients to pick up new config on next access
        if "cortex_url" in kwargs:
            self._llm = None
        if "redis_url" in kwargs:
            self._cache = None
        if "postgres_url" in kwargs:
            self._db = None
        if "edgeserver_url" in kwargs:
            self._system = None


def get_service_registry() -> ServiceRegistry:
    """Get the singleton ServiceRegistry instance."""
    return ServiceRegistry()
