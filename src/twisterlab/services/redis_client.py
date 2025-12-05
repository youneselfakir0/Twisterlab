"""
Redis Cache Client

Concrete implementation of CacheClient for Redis.
Connects to EdgeServer Redis at 192.168.0.30:6379.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional
from urllib.parse import urlparse

from .base import (
    CacheClient,
    CacheStats,
    ServiceHealth,
    ServiceStatus,
)

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import aioredis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        logger.warning("redis/aioredis not available - cache client will use fallback mode")


class RedisServiceClient(CacheClient):
    """
    Cache client for Redis.
    
    Provides async access to Redis for caching and pub/sub.
    """
    
    def __init__(self, url: str = "redis://192.168.0.30:6379"):
        self._url = url
        parsed = urlparse(url)
        self._host = parsed.hostname or "192.168.0.30"
        self._port = parsed.port or 6379
        self._client: Optional[aioredis.Redis] = None
        logger.info(f"RedisServiceClient initialized: {self._host}:{self._port}")
    
    @property
    def name(self) -> str:
        return "redis"
    
    async def _get_client(self) -> "aioredis.Redis":
        """Get or create Redis client."""
        if self._client is None:
            if not REDIS_AVAILABLE:
                raise RuntimeError("Redis client not available")
            self._client = aioredis.from_url(self._url, decode_responses=True)
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not REDIS_AVAILABLE:
            return None
        try:
            client = await self._get_client()
            return await client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value with optional TTL."""
        if not REDIS_AVAILABLE:
            return False
        try:
            client = await self._get_client()
            if ttl:
                await client.setex(key, ttl, value)
            else:
                await client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        if not REDIS_AVAILABLE:
            return False
        try:
            client = await self._get_client()
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not REDIS_AVAILABLE:
            return False
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """List keys matching pattern."""
        if not REDIS_AVAILABLE:
            return []
        try:
            client = await self._get_client()
            return await client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []
    
    async def get_stats(self) -> CacheStats:
        """Get Redis statistics."""
        if not REDIS_AVAILABLE:
            return CacheStats()
        try:
            client = await self._get_client()
            info = await client.info()
            
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            
            return CacheStats(
                connected_clients=info.get("connected_clients", 0),
                used_memory=info.get("used_memory_human", "0B"),
                total_keys=await client.dbsize(),
                hits=hits,
                misses=misses,
                hit_rate=hit_rate,
            )
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return CacheStats()
    
    async def health_check(self) -> ServiceHealth:
        """Check Redis health."""
        if not REDIS_AVAILABLE:
            return ServiceHealth(
                name=self.name,
                status=ServiceStatus.DEGRADED,
                message="redis library not available"
            )
        
        try:
            start = time.perf_counter()
            client = await self._get_client()
            pong = await client.ping()
            elapsed = (time.perf_counter() - start) * 1000
            
            if pong:
                info = await client.info("server")
                return ServiceHealth(
                    name=self.name,
                    status=ServiceStatus.CONNECTED,
                    latency_ms=elapsed,
                    message="PONG",
                    metadata={
                        "redis_version": info.get("redis_version"),
                        "uptime_days": info.get("uptime_in_days"),
                    }
                )
            else:
                return ServiceHealth(
                    name=self.name,
                    status=ServiceStatus.DEGRADED,
                    latency_ms=elapsed,
                    message="No PONG received"
                )
        except Exception as e:
            return ServiceHealth(
                name=self.name,
                status=ServiceStatus.DISCONNECTED,
                message=str(e)
            )
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
