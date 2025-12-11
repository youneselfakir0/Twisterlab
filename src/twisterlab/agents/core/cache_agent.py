"""
Cache Agent

MCP-agnostic agent for Redis cache operations.
Provides capabilities for managing cached data.
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


class CacheAgent(TwisterAgent):
    """
    Agent for Redis cache operations.

    Provides capabilities for:
    - Getting/setting cache values
    - Listing keys
    - Cache statistics
    """

    @property
    def name(self) -> str:
        return "cache"

    @property
    def description(self) -> str:
        return "Redis cache operations and management"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="cache_get",
                description="Get a value from cache",
                handler="handle_cache_get",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "key",
                        ParamType.STRING,
                        "Cache key to retrieve",
                    ),
                ],
                tags=["cache", "read"],
            ),
            AgentCapability(
                name="cache_set",
                description="Set a value in cache",
                handler="handle_cache_set",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        "key",
                        ParamType.STRING,
                        "Cache key",
                    ),
                    CapabilityParam(
                        "value",
                        ParamType.STRING,
                        "Value to store",
                    ),
                    CapabilityParam(
                        "ttl",
                        ParamType.INTEGER,
                        "Time to live in seconds",
                        required=False,
                    ),
                ],
                tags=["cache", "write"],
            ),
            AgentCapability(
                name="cache_delete",
                description="Delete a key from cache",
                handler="handle_cache_delete",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        "key",
                        ParamType.STRING,
                        "Cache key to delete",
                    ),
                ],
                tags=["cache", "write"],
            ),
            AgentCapability(
                name="cache_keys",
                description="List cache keys matching a pattern",
                handler="handle_cache_keys",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "pattern",
                        ParamType.STRING,
                        "Pattern to match (e.g., 'user:*')",
                        required=False,
                        default="*",
                    ),
                ],
                tags=["cache", "list"],
            ),
            AgentCapability(
                name="cache_stats",
                description="Get cache statistics",
                handler="handle_cache_stats",
                capability_type=CapabilityType.QUERY,
                tags=["cache", "stats"],
            ),
        ]

    # =========================================================================
    # Handler Methods
    # =========================================================================

    async def handle_cache_get(self, key: str) -> AgentResponse:
        """Get a value from cache."""
        try:
            cache = self.registry.get_cache()
            value = await cache.get(key)

            if value is None:
                return AgentResponse(
                    success=True,
                    data={
                        "key": key,
                        "found": False,
                        "value": None,
                    },
                )

            return AgentResponse(
                success=True,
                data={
                    "key": key,
                    "found": True,
                    "value": value,
                },
            )
        except Exception as e:
            logger.exception(f"Cache get failed for key {key}")
            return AgentResponse(success=False, error=str(e))

    async def handle_cache_set(
        self, key: str, value: str, ttl: int = None
    ) -> AgentResponse:
        """Set a value in cache."""
        try:
            cache = self.registry.get_cache()
            success = await cache.set(key, value, ttl=ttl)

            return AgentResponse(
                success=success,
                data={
                    "key": key,
                    "stored": success,
                    "ttl": ttl,
                },
            )
        except Exception as e:
            logger.exception(f"Cache set failed for key {key}")
            return AgentResponse(success=False, error=str(e))

    async def handle_cache_delete(self, key: str) -> AgentResponse:
        """Delete a key from cache."""
        try:
            cache = self.registry.get_cache()
            deleted = await cache.delete(key)

            return AgentResponse(
                success=True,
                data={
                    "key": key,
                    "deleted": deleted,
                },
            )
        except Exception as e:
            logger.exception(f"Cache delete failed for key {key}")
            return AgentResponse(success=False, error=str(e))

    async def handle_cache_keys(self, pattern: str = "*") -> AgentResponse:
        """List cache keys."""
        try:
            cache = self.registry.get_cache()
            keys = await cache.keys(pattern)

            return AgentResponse(
                success=True,
                data={
                    "pattern": pattern,
                    "keys": keys,
                    "count": len(keys),
                },
            )
        except Exception as e:
            logger.exception(f"Cache keys failed for pattern {pattern}")
            return AgentResponse(success=False, error=str(e))

    async def handle_cache_stats(self) -> AgentResponse:
        """Get cache statistics."""
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
                },
            )
        except Exception as e:
            logger.exception("Cache stats failed")
            return AgentResponse(success=False, error=str(e))
