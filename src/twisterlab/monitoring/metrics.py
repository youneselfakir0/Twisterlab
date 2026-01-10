"""Prometheus metrics definitions for TwisterLab.

This module defines custom metrics for monitoring the TwisterLab API and agents.
Metrics are exposed at /metrics endpoint and scraped by Prometheus.
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable

from prometheus_client import Counter, Gauge, Histogram, Info

# =============================================================================
# HTTP Metrics (supplementary to prometheus-fastapi-instrumentator)
# =============================================================================

HTTP_REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# =============================================================================
# Agent Metrics
# =============================================================================

AGENT_COUNT = Gauge(
    "agent_count_total", "Total number of registered agents", ["agent_type", "status"]
)

# Active agents gauge (for dashboards)
ACTIVE_AGENTS = Gauge(
    "active_agents_count", "Number of currently active agents"
)

AGENT_EXECUTIONS = Counter(
    "agent_execution_total",
    "Total agent executions",
    ["agent_name", "agent_type", "status"],
)

# Alias for dashboard compatibility: agent_calls_total
AGENT_CALLS = Counter(
    "agent_calls_total",
    "Total agent calls (alias for agent_execution_total)",
    ["agent_name", "capability"],
)

AGENT_EXECUTION_DURATION = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name", "agent_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

# Alias for dashboard compatibility: agent_latency_seconds
AGENT_LATENCY = Histogram(
    "agent_latency_seconds",
    "Agent call latency in seconds",
    ["agent_name", "capability"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

AGENT_ERRORS = Counter(
    "agent_errors_total",
    "Total agent errors",
    ["agent_name", "agent_type", "error_type"],
)

# =============================================================================
# Maestro/Orchestration Metrics
# =============================================================================

MAESTRO_DECISIONS = Counter(
    "maestro_decisions_total",
    "Total decisions made by Maestro orchestrator",
    ["decision_type", "outcome"],
)

MAESTRO_ACTIVE_WORKFLOWS = Gauge(
    "maestro_active_workflows",
    "Number of active Maestro workflows"
)

# =============================================================================
# Ticket/Incident Resolution Metrics
# =============================================================================

TICKETS_RESOLVED = Counter(
    "tickets_resolved_total",
    "Total tickets resolved",
    ["resolution_type", "agent_name", "priority"],
)

TICKET_RESOLUTION_TIME = Histogram(
    "ticket_resolution_time_seconds",
    "Time to resolve tickets in seconds",
    ["priority"],
    buckets=(30, 60, 120, 300, 600, 1800, 3600, 7200),
)

# =============================================================================
# Command Execution Metrics (DesktopCommander)
# =============================================================================

COMMANDS_EXECUTED = Counter(
    "commands_executed_total",
    "Total commands executed by DesktopCommander",
    ["command_type", "status"],
)

COMMAND_DURATION = Histogram(
    "command_duration_seconds",
    "Command execution duration in seconds",
    ["command_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

# =============================================================================
# System Metrics
# =============================================================================

APP_INFO = Info("twisterlab_app", "TwisterLab application information")

# Set app info at module load
APP_INFO.info({"version": "3.5.0", "name": "twisterlab", "environment": "production"})

# =============================================================================
# Helper Functions
# =============================================================================


def track_agent_execution(
    agent_name: str, agent_type: str, duration: float, success: bool = True,
    capability: str = "execute"
) -> None:
    """Track an agent execution with its duration and status.

    Args:
        agent_name: Name of the agent
        agent_type: Type of the agent (e.g., 'chat', 'code', 'browser')
        duration: Execution duration in seconds
        success: Whether the execution was successful
        capability: The capability that was called
    """
    status = "success" if success else "failure"
    
    # Original metrics
    AGENT_EXECUTIONS.labels(
        agent_name=agent_name, agent_type=agent_type, status=status
    ).inc()

    AGENT_EXECUTION_DURATION.labels(
        agent_name=agent_name, agent_type=agent_type
    ).observe(duration)
    
    # Dashboard-compatible metrics (aliases)
    AGENT_CALLS.labels(
        agent_name=agent_name, capability=capability
    ).inc()
    
    AGENT_LATENCY.labels(
        agent_name=agent_name, capability=capability
    ).observe(duration)


def track_agent_call(
    agent_name: str, capability: str, duration: float, success: bool = True,
    error_type: str = None
) -> None:
    """Track an agent call (dashboard-compatible helper).

    Args:
        agent_name: Name of the agent
        capability: The capability that was called
        duration: Call duration in seconds
        success: Whether the call was successful
        error_type: Type of error if failed
    """
    # Dashboard-compatible metrics
    AGENT_CALLS.labels(agent_name=agent_name, capability=capability).inc()
    AGENT_LATENCY.labels(agent_name=agent_name, capability=capability).observe(duration)
    
    if not success and error_type:
        AGENT_ERRORS.labels(
            agent_name=agent_name, agent_type="core", error_type=error_type
        ).inc()


def track_agent_error(
    agent_name: str, agent_type: str, error_type: str = "unknown"
) -> None:
    """Track an agent error.

    Args:
        agent_name: Name of the agent
        agent_type: Type of the agent
        error_type: Type of error (e.g., 'timeout', 'connection', 'validation')
    """
    AGENT_ERRORS.labels(
        agent_name=agent_name, agent_type=agent_type, error_type=error_type
    ).inc()


def track_maestro_decision(decision_type: str, outcome: str = "success") -> None:
    """Track a Maestro orchestration decision.
    
    Args:
        decision_type: Type of decision (e.g., 'dispatch', 'escalate', 'resolve')
        outcome: Outcome of the decision
    """
    MAESTRO_DECISIONS.labels(decision_type=decision_type, outcome=outcome).inc()


def track_ticket_resolved(
    resolution_type: str, agent_name: str, priority: str = "normal", 
    resolution_time: float = None
) -> None:
    """Track a resolved ticket.
    
    Args:
        resolution_type: How the ticket was resolved
        agent_name: Agent that resolved it
        priority: Ticket priority
        resolution_time: Time taken to resolve in seconds
    """
    TICKETS_RESOLVED.labels(
        resolution_type=resolution_type, agent_name=agent_name, priority=priority
    ).inc()
    
    if resolution_time is not None:
        TICKET_RESOLUTION_TIME.labels(priority=priority).observe(resolution_time)


def track_command_executed(command_type: str, success: bool = True, duration: float = None) -> None:
    """Track a command execution by DesktopCommander.
    
    Args:
        command_type: Type of command
        success: Whether it succeeded
        duration: Execution duration in seconds
    """
    status = "success" if success else "failure"
    COMMANDS_EXECUTED.labels(command_type=command_type, status=status).inc()
    
    if duration is not None:
        COMMAND_DURATION.labels(command_type=command_type).observe(duration)


def set_active_agents(count: int) -> None:
    """Set the number of active agents."""
    ACTIVE_AGENTS.set(count)


def set_maestro_workflows(count: int) -> None:
    """Set the number of active Maestro workflows."""
    MAESTRO_ACTIVE_WORKFLOWS.set(count)


def update_agent_count(agent_type: str, status: str, count: int) -> None:
    """Update the gauge for agent count.

    Args:
        agent_type: Type of agents
        status: Status of agents (e.g., 'active', 'idle', 'error')
        count: Current count
    """
    AGENT_COUNT.labels(agent_type=agent_type, status=status).set(count)


@contextmanager
def measure_agent_execution(agent_name: str, agent_type: str):
    """Context manager to measure agent execution time.

    Usage:
        with measure_agent_execution("my_agent", "chat"):
            # agent execution code
            pass
    """
    start_time = time.perf_counter()
    success = True
    try:
        yield
    except Exception as e:
        success = False
        track_agent_error(agent_name, agent_type, type(e).__name__)
        raise
    finally:
        duration = time.perf_counter() - start_time
        track_agent_execution(agent_name, agent_type, duration, success)


def agent_metrics(agent_name: str, agent_type: str) -> Callable:
    """Decorator to automatically track agent execution metrics.

    Usage:
        @agent_metrics("my_agent", "chat")
        async def execute_agent():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with measure_agent_execution(agent_name, agent_type):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with measure_agent_execution(agent_name, agent_type):
                return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def register_with_app(app) -> None:
    """Register metrics middleware with FastAPI app.

    This adds automatic HTTP request tracking for all endpoints.

    Args:
        app: FastAPI application instance
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class MetricsMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start_time = time.perf_counter()

            response = await call_next(request)

            duration = time.perf_counter() - start_time

            # Get endpoint path (use route path if available for consistency)
            endpoint = request.url.path
            if hasattr(request, "scope") and "route" in request.scope:
                route = request.scope.get("route")
                if route and hasattr(route, "path"):
                    endpoint = route.path

            # Track metrics
            HTTP_REQUESTS.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            return response

    app.add_middleware(MetricsMiddleware)


def get_metric_values(metric_names: list[str] | None = None) -> dict[str, float | None]:
    """Return current metric values for requested metric names.

    If metric_names is None, return all standard metrics registered by this module.

    Args:
        metric_names: List of metric names to retrieve. If None, returns default metrics.

    Returns:
        Dictionary mapping metric names to their current values
    """
    from prometheus_client import REGISTRY

    metrics: dict[str, float | None] = {}
    if metric_names is None:
        metric_names = ["agent_count_total", "agent_errors_total"]

    for name in metric_names:
        try:
            # REGISTRY.get_sample_value returns the latest value for the metric name
            value = REGISTRY.get_sample_value(name)
            # If no value (not yet sampled), but metric exists, return 0
            metrics[name] = float(value) if value is not None else 0.0
        except Exception:
            metrics[name] = None
    return metrics
