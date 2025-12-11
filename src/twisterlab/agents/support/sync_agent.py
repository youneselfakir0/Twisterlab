"""
SyncAgent - Data Synchronization Agent
========================================

Maintains data consistency across TwisterLab's distributed components:
PostgreSQL, Redis cache, and agent state.

Author: Claude + Copilot Collaborative Development
Version: 1.0.0-alpha.1
License: Apache 2.0
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import TwisterAgent, accepts_context_or_task

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sync_agent")


# ============================================================================
# SYNC STATUS
# ============================================================================


class SyncStatus:
    """Sync operation status constants"""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    INCONSISTENT = "inconsistent"
    CONSISTENT = "consistent"


# ============================================================================
# SYNC AGENT
# ============================================================================


class SyncAgent(TwisterAgent):
    """
    Agent for maintaining data consistency across system components.

    Features:
    - PostgreSQL ↔ Redis cache synchronization
    - Agent state propagation
    - Conflict detection and resolution
    - Data integrity verification
    - Cache invalidation

    Sync Types:
    - Real-time: Ticket status, agent state
    - Scheduled: SOPs, devices (every 5 minutes)
    - On-demand: Manual sync, post-deployment
    """

    def __init__(self):
        super().__init__(
            name="sync-agent",
            display_name="Data Synchronization Agent",
            description="Maintains consistency across PostgreSQL, Redis, and agent state",
            model="llama-3.2",
            temperature=0.2,
            tools=self._define_tools(),
        )

        # Redis connection (mock for now)
        self.redis_client = None
        self.redis_connected = False

        # Sync statistics
        self.sync_stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "last_sync": None,
            "last_sync_duration": 0.0,
        }

        # Cache for sync state
        self.sync_state = {
            "sops_last_sync": None,
            "devices_last_sync": None,
            "agent_state_last_sync": None,
        }

        logger.info("SyncAgent initialized")

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define MCP tools for sync operations"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "sync_all",
                    "description": "Synchronize all data sources (SOPs, devices, agent state)",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "sync_sops",
                    "description": "Sync SOPs from PostgreSQL to Redis cache",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "sync_devices",
                    "description": "Sync device registry from PostgreSQL to Redis cache",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "sync_agent_state",
                    "description": "Sync agent state to Redis for distributed access",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "invalidate_cache",
                    "description": "Invalidate cache keys matching a pattern",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Redis key pattern (e.g., 'sop:*', 'device:*')",
                            }
                        },
                        "required": ["pattern"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "verify_consistency",
                    "description": "Verify data consistency between database and cache",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

    async def _ensure_redis_connection(self) -> bool:
        """
        Ensure Redis connection is established.

        For v1.0, this simulates Redis connection.
        In production, use redis.asyncio.
        """
        if not self.redis_connected:
            try:
                # Mock Redis connection for now
                # In production: self.redis_client = await aioredis.from_url(...)
                self.redis_client = MockRedisClient()
                self.redis_connected = True
                logger.info("Redis connection established (mock)")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return False
        return True

    @accepts_context_or_task
    async def execute(
        self, task_or_context, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute sync operation.

        Args:
            task: Task description
            context: Operation context with parameters

        Returns:
            Sync result with status and details
        """
        try:
            # Normalize inputs for both calling conventions
            if context is None and isinstance(task_or_context, dict):
                context = task_or_context
                task = context.get("operation", "sync_all")
            else:
                task = task_or_context
            start_time = datetime.now(timezone.utc)
            logger.info(f"SyncAgent executing: {task}")

            # Ensure Redis connection
            if not await self._ensure_redis_connection():
                return {
                    "status": SyncStatus.FAILED,
                    "error": "Redis connection unavailable",
                }

            # Parse operation
            context = context or {}
            operation = context.get("operation", "sync_all")

            # Route to appropriate handler
            if operation == "sync_all":
                result = await self._sync_all()
            elif operation == "sync_sops":
                result = await self._sync_sops()
            elif operation == "sync_devices":
                result = await self._sync_devices()
            elif operation == "sync_agent_state":
                result = await self._sync_agent_state()
            elif operation == "invalidate_cache":
                pattern = context.get("pattern", "*")
                result = await self._invalidate_cache(pattern)
            elif operation == "verify_consistency":
                result = await self._verify_consistency()
            else:
                result = {
                    "status": SyncStatus.FAILED,
                    "error": f"Unknown operation: {operation}",
                }

            # Update statistics
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.sync_stats["total_syncs"] += 1
            self.sync_stats["last_sync_duration"] = duration

            if result["status"] == SyncStatus.SUCCESS:
                self.sync_stats["successful_syncs"] += 1
            else:
                self.sync_stats["failed_syncs"] += 1

            self.sync_stats["last_sync"] = datetime.now(timezone.utc).isoformat()

            result["duration_seconds"] = round(duration, 3)

            return result

        except Exception as e:
            logger.error(f"Error in sync execution: {e}", exc_info=True)
            return {
                "status": SyncStatus.FAILED,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def _sync_all(self) -> Dict[str, Any]:
        """
        Sync all data sources.

        Synchronizes:
        - SOPs (PostgreSQL → Redis)
        - Devices (PostgreSQL → Redis)
        - Agent State (Memory → Redis)
        """
        logger.info("Starting full system sync")

        results = {
            "sops": await self._sync_sops(),
            "devices": await self._sync_devices(),
            "agent_state": await self._sync_agent_state(),
        }

        # Determine overall status
        statuses = [r["status"] for r in results.values()]

        if all(s == SyncStatus.SUCCESS for s in statuses):
            overall_status = SyncStatus.SUCCESS
        elif any(s == SyncStatus.SUCCESS for s in statuses):
            overall_status = SyncStatus.PARTIAL
        else:
            overall_status = SyncStatus.FAILED

        return {
            "status": overall_status,
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _sync_sops(self) -> Dict[str, Any]:
        """
        Sync SOPs from PostgreSQL to Redis cache.

        Syncs:
        - Individual SOPs with 1 hour TTL
        - Category index
        """
        try:
            logger.info("Syncing SOPs to cache")

            # Mock SOP data (in production, query from database)
            mock_sops = [
                {
                    "id": "sop-001",
                    "title": "Password Reset Procedure",
                    "category": "IAM",
                    "steps": ["Verify identity", "Reset password", "Notify user"],
                    "keywords": ["password", "reset", "account"],
                },
                {
                    "id": "sop-002",
                    "title": "Software Installation",
                    "category": "Desktop",
                    "steps": ["Check compatibility", "Install", "Verify"],
                    "keywords": ["install", "software", "application"],
                },
                {
                    "id": "sop-003",
                    "title": "Network Troubleshooting",
                    "category": "Network",
                    "steps": ["Check connectivity", "Verify config", "Test"],
                    "keywords": ["network", "connectivity", "troubleshoot"],
                },
            ]

            synced_count = 0

            # Cache each SOP
            for sop in mock_sops:
                cache_key = f"sop:{sop['id']}"
                await self.redis_client.setex(
                    cache_key, 3600, json.dumps(sop)
                )  # 1 hour TTL
                synced_count += 1

            # Build and cache category index
            categories = {}
            for sop in mock_sops:
                category = sop["category"]
                if category not in categories:
                    categories[category] = []
                categories[category].append(sop["id"])

            await self.redis_client.setex(
                "sops:categories", 3600, json.dumps(categories)
            )

            # Update sync state
            self.sync_state["sops_last_sync"] = datetime.now(timezone.utc).isoformat()

            logger.info(f"Synced {synced_count} SOPs to cache")

            return {
                "status": SyncStatus.SUCCESS,
                "synced_count": synced_count,
                "categories": len(categories),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error syncing SOPs: {e}", exc_info=True)
            return {"status": SyncStatus.FAILED, "error": str(e)}

    async def _sync_devices(self) -> Dict[str, Any]:
        """
        Sync device registry from PostgreSQL to Redis.

        Syncs device data with 10 minute TTL.
        """
        try:
            logger.info("Syncing devices to cache")

            # Mock device data
            mock_devices = [
                {
                    "device_id": "DESKTOP-001",
                    "hostname": "WKS-SALES-01",
                    "os": "Windows 11",
                    "is_online": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "device_id": "DESKTOP-002",
                    "hostname": "WKS-IT-05",
                    "os": "Windows 10",
                    "is_online": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "device_id": "SERVER-001",
                    "hostname": "SRV-DC-01",
                    "os": "Windows Server 2022",
                    "is_online": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
            ]

            synced_count = 0

            for device in mock_devices:
                cache_key = f"device:{device['device_id']}"
                await self.redis_client.setex(
                    cache_key, 600, json.dumps(device)
                )  # 10 minutes TTL
                synced_count += 1

            # Update sync state
            self.sync_state["devices_last_sync"] = datetime.now(
                timezone.utc
            ).isoformat()

            logger.info(f"Synced {synced_count} devices to cache")

            return {
                "status": SyncStatus.SUCCESS,
                "synced_count": synced_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error syncing devices: {e}", exc_info=True)
            return {"status": SyncStatus.FAILED, "error": str(e)}

    async def _sync_agent_state(self) -> Dict[str, Any]:
        """
        Sync agent state to Redis for distributed access.

        Syncs current agent states with 1 minute TTL.
        """
        try:
            logger.info("Syncing agent state")

            # Mock agent states (in production, get from Maestro)
            agent_states = {
                "classifier": {
                    "status": "healthy",
                    "load": 2,
                    "last_activity": datetime.now(timezone.utc).isoformat(),
                },
                "resolver": {
                    "status": "healthy",
                    "load": 1,
                    "last_activity": datetime.now(timezone.utc).isoformat(),
                },
                "desktop_commander": {
                    "status": "healthy",
                    "load": 0,
                    "last_activity": datetime.now(timezone.utc).isoformat(),
                },
                "maestro": {
                    "status": "healthy",
                    "tickets_routed": 42,
                    "last_activity": datetime.now(timezone.utc).isoformat(),
                },
            }

            await self.redis_client.setex(
                "agents:state", 60, json.dumps(agent_states)  # 1 minute TTL
            )

            # Update sync state
            self.sync_state["agent_state_last_sync"] = datetime.now(
                timezone.utc
            ).isoformat()

            logger.info(f"Synced state for {len(agent_states)} agents")

            return {
                "status": SyncStatus.SUCCESS,
                "agents_synced": len(agent_states),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error syncing agent state: {e}", exc_info=True)
            return {"status": SyncStatus.FAILED, "error": str(e)}

    async def _invalidate_cache(self, pattern: str) -> Dict[str, Any]:
        """
        Invalidate cache keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., 'sop:*', 'device:*')
        """
        try:
            logger.info(f"Invalidating cache pattern: {pattern}")

            # Find matching keys
            matching_keys = await self.redis_client.keys(pattern)

            # Delete keys
            invalidated_count = 0
            if matching_keys:
                for key in matching_keys:
                    await self.redis_client.delete(key)
                    invalidated_count += 1

            logger.info(f"Invalidated {invalidated_count} cache keys")

            return {
                "status": SyncStatus.SUCCESS,
                "invalidated_count": invalidated_count,
                "pattern": pattern,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}", exc_info=True)
            return {"status": SyncStatus.FAILED, "error": str(e)}

    async def _verify_consistency(self) -> Dict[str, Any]:
        """
        Verify data consistency between database and cache.

        Checks:
        - SOPs: Database vs Cache
        - Devices: Database vs Cache
        - Missing cache entries
        - Data mismatches
        """
        try:
            logger.info("Verifying data consistency")

            inconsistencies = []

            # Verify SOPs (mock check)
            sop_ids = ["sop-001", "sop-002", "sop-003"]

            for sop_id in sop_ids:
                cache_key = f"sop:{sop_id}"
                cached_data = await self.redis_client.get(cache_key)

                if not cached_data:
                    inconsistencies.append(
                        {"type": "missing_cache", "entity": "sop", "id": sop_id}
                    )

            # Verify devices (mock check)
            device_ids = ["DESKTOP-001", "DESKTOP-002", "SERVER-001"]

            for device_id in device_ids:
                cache_key = f"device:{device_id}"
                cached_data = await self.redis_client.get(cache_key)

                if not cached_data:
                    inconsistencies.append(
                        {"type": "missing_cache", "entity": "device", "id": device_id}
                    )

            # Determine status
            if inconsistencies:
                logger.warning(f"Found {len(inconsistencies)} inconsistencies")
                status = SyncStatus.INCONSISTENT
            else:
                status = SyncStatus.CONSISTENT

            return {
                "status": status,
                "inconsistencies": inconsistencies,
                "checked_sops": len(sop_ids),
                "checked_devices": len(device_ids),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error verifying consistency: {e}", exc_info=True)
            return {"status": SyncStatus.FAILED, "error": str(e)}

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get sync statistics"""
        return {
            **self.sync_stats,
            "sync_state": self.sync_state,
            "redis_connected": self.redis_connected,
        }

    def health_check(self) -> Dict[str, Any]:
        """Agent health check"""
        return {
            "status": "healthy" if self.redis_connected else "degraded",
            "agent": self.name,
            "redis_connected": self.redis_connected,
            "sync_stats": self.sync_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ============================================================================
# MOCK REDIS CLIENT (for testing without actual Redis)
# ============================================================================


class MockRedisClient:
    """Mock Redis client for testing"""

    def __init__(self):
        self.data = {}
        self.ttls = {}

    async def setex(self, key: str, ttl: int, value: str):
        """Set key with expiration"""
        self.data[key] = value
        self.ttls[key] = ttl

    async def get(self, key: str) -> Optional[str]:
        """Get key value"""
        return self.data.get(key)

    async def delete(self, *keys: str):
        """Delete keys"""
        for key in keys:
            self.data.pop(key, None)
            self.ttls.pop(key, None)

    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        import fnmatch

        return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":

    async def main():
        sync_agent = SyncAgent()

        # Test full sync
        print("\n=== Full System Sync ===")
        result = await sync_agent.execute("Sync all data", {"operation": "sync_all"})
        print(json.dumps(result, indent=2))

        # Test cache invalidation
        print("\n=== Cache Invalidation ===")
        result = await sync_agent.execute(
            "Invalidate cache", {"operation": "invalidate_cache", "pattern": "sop:*"}
        )
        print(json.dumps(result, indent=2))

        # Test consistency verification
        print("\n=== Consistency Verification ===")
        result = await sync_agent.execute(
            "Verify consistency", {"operation": "verify_consistency"}
        )
        print(json.dumps(result, indent=2))

        # Get stats
        print("\n=== Sync Statistics ===")
        print(json.dumps(sync_agent.get_sync_stats(), indent=2))

    asyncio.run(main())
