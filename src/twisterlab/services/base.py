"""
Service Interfaces (Ports) for TwisterLab

These abstract base classes define contracts for external services.
Concrete implementations (adapters) can be swapped without changing agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime


class ServiceStatus(Enum):
    """Status of a service connection."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status of a service."""

    name: str
    status: ServiceStatus
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    last_check: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        return self.status == ServiceStatus.CONNECTED


# =============================================================================
# LLM Client Interface
# =============================================================================


@dataclass
class LLMResponse:
    """Response from an LLM query."""

    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMessage:
    """Chat message for LLM."""

    role: str  # "system", "user", "assistant"
    content: str


class LLMClient(ABC):
    """
    Abstract interface for LLM services.

    Implementations: CortexClient (Ollama), OpenAIClient, etc.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Service name identifier."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion from a prompt."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Chat completion with message history."""
        pass

    @abstractmethod
    async def stream(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        pass

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        pass

    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """Check service health."""
        pass


# =============================================================================
# Cache Client Interface
# =============================================================================


@dataclass
class CacheStats:
    """Cache statistics."""

    connected_clients: int = 0
    used_memory: str = "0B"
    total_keys: int = 0
    hits: int = 0
    misses: int = 0
    hit_rate: float = 0.0


class CacheClient(ABC):
    """
    Abstract interface for cache services.

    Implementations: RedisClient, MemcachedClient, etc.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Service name identifier."""
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value with optional TTL in seconds."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """List keys matching pattern."""
        pass

    @abstractmethod
    async def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        pass

    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """Check service health."""
        pass


# =============================================================================
# Database Client Interface
# =============================================================================


@dataclass
class QueryResult:
    """Result of a database query."""

    rows: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class DBStats:
    """Database statistics."""

    active_connections: int = 0
    total_connections: int = 0
    database_size: str = "0B"
    table_count: int = 0
    uptime: str = "0s"


class DBClient(ABC):
    """
    Abstract interface for database services.

    Implementations: PostgresClient, MySQLClient, etc.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Service name identifier."""
        pass

    @abstractmethod
    async def query(
        self, sql: str, params: Optional[List[Any]] = None, read_only: bool = True
    ) -> QueryResult:
        """Execute a SQL query."""
        pass

    @abstractmethod
    async def execute(self, sql: str, params: Optional[List[Any]] = None) -> int:
        """Execute a SQL statement, return affected rows."""
        pass

    @abstractmethod
    async def get_tables(self) -> List[str]:
        """List all tables."""
        pass

    @abstractmethod
    async def get_table_schema(self, table: str) -> Dict[str, Any]:
        """Get schema for a table."""
        pass

    @abstractmethod
    async def get_stats(self) -> DBStats:
        """Get database statistics."""
        pass

    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """Check service health."""
        pass


# =============================================================================
# System Client Interface (for Docker, Host metrics, etc.)
# =============================================================================


class ContainerState(Enum):
    """State of a container."""

    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    STARTING = "starting"
    UNKNOWN = "unknown"


@dataclass
class ContainerInfo:
    """Docker container information."""

    id: str
    name: str
    image: str
    state: ContainerState = ContainerState.UNKNOWN
    ports: Dict[str, Any] = field(default_factory=dict)
    created: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceInfo:
    """Service information."""

    name: str
    status: str
    replicas: int = 1
    ports: Dict[str, int] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System metrics."""

    cpu_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    memory_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    disk_percent: float = 0.0
    uptime_seconds: int = 0
    container_count: int = 0


class SystemClient(ABC):
    """
    Abstract interface for system/infrastructure services.

    Implementations: DockerClient, SSHClient, etc.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Service name identifier."""
        pass

    @abstractmethod
    async def get_containers(self) -> List[ContainerInfo]:
        """List Docker containers."""
        pass

    @abstractmethod
    async def get_container_logs(self, container: str, lines: int = 100) -> List[str]:
        """Get container logs."""
        pass

    @abstractmethod
    async def get_metrics(self) -> SystemMetrics:
        """Get system metrics."""
        pass

    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """Check service health."""
        pass
