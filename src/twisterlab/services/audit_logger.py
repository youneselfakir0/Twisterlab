"""
AuditLoggerService - Contract and Abstract Definition

This service provides the standardized contract for logging all significant execution events
(Tool Calls, Agent Runs). All concrete implementations must adhere to this structure.
---
Dependencies Required:
- Database Session Access (DBClient)
- Async Cache/Messaging Client (RedisServiceClient)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
# From src/twisterlab/storage/base: Assume an asynchronous session context exists.

class AuditLoggerService(ABC):
    """Abstract class defining the required contract for any service that logs audit events."""

    @abstractmethod
    async def log_start(self, run_id: str, component: str, action: str, input_data: Dict[str, Any]) -> None:
        """Logs the commencement of a measurable process segment. Must record start time."""
        pass

    @abstractmethod
    async def log_end(self, run_id: str, component: str, action: str, status: str, duration_ms: float, output_data: Dict[str, Any]) -> None:
        """Logs the successful conclusion of a process segment. Must record final data."""
        pass

    @abstractmethod
    async def log_error(self, run_id: str, component: str, action: str, error: Exception, input_data: Dict[str, Any]) -> None:
        """Logs explicit failures, ensuring the system does not crash and logs diagnostic information."""
        pass

    @abstractmethod
    async def log_manual_event(self, run_id: str, component: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Logs non-critical status updates (e.g., 'Waiting for external resource')."""
        pass