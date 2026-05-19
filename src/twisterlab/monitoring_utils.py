"""
TwisterLab Monitoring Utilities
Provides specialized Prometheus metrics for the Agent fleet and Orchestration layer.
"""

import logging
import time
import functools
import re
from typing import Optional, Callable, Any

try:
    from prometheus_client import Counter, Histogram, Gauge
except ImportError:
    # Graceful fallback if prometheus_client is not installed
    class MockMetric:
        def labels(self, *args, **kwargs): return self
        def inc(self, amount=1): pass
        def observe(self, value): pass
        def set(self, value): pass
    
    Counter = Histogram = Gauge = lambda *args, **kwargs: MockMetric()

logger = logging.getLogger(__name__)

# --- METRIC DEFINITIONS ---

# 1. Agent Resolution Metrics
AGENT_RESOLUTION_TOTAL = Counter(
    "twisterlab_agent_resolution_total",
    "Total count of agent capability resolutions",
    ["requirement", "agent", "status"] # status: success | failed | skipped
)

# 2. Mission Performance Metrics
MISSION_EXECUTION_SECONDS = Histogram(
    "twisterlab_mission_duration_seconds",
    "Duration of orchestrated missions in seconds",
    ["category", "priority"],
    buckets=(1, 2, 5, 10, 30, 60, 120, 300, 600)
)

# 3. Agent Execution Metrics (from Adapter)
AGENT_EXECUTION_SECONDS = Histogram(
    "twisterlab_agent_call_duration_seconds",
    "Duration of individual agent tool calls in seconds",
    ["agent", "tool"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# 4. Agent Error Metrics
AGENT_ERRORS_TOTAL = Counter(
    "twisterlab_agent_errors_total",
    "Total count of agent-specific failures",
    ["agent", "error_code"]
)

# 5. Registry Health Gauge
REGISTRY_AGENTS_ONLINE = Gauge(
    "twisterlab_registry_agents_online",
    "Number of agents currently initialized and online"
)

# 6. Self-Healing Events Counter
HEALING_EVENTS_TOTAL = Counter(
    "twisterlab_healing_events_total",
    "Total count of self-healing events by category, capability requirement, and outcome status",
    ["category", "requirement", "status"]
)

# --- UTILITY FUNCTIONS ---

def record_resolution(requirement: str, agent: str, status: str):
    """Logs an agent resolution event."""
    try:
        AGENT_RESOLUTION_TOTAL.labels(
            requirement=requirement, 
            agent=agent, 
            status=status
        ).inc()
    except (AttributeError, RuntimeError) as e:
        logger.debug(f"Failed to record resolution metric: {e}")

def record_agent_error(agent: str, error_code: str):
    """Logs an agent error event."""
    try:
        AGENT_ERRORS_TOTAL.labels(
            agent=agent,
            error_code=error_code
        ).inc()
    except (AttributeError, RuntimeError, KeyError) as e:
        logger.debug(f"Failed to record error metric: {e}")

def mission_timer(category: str, priority: str):
    """Decorator or context manager to time a mission."""
    return MISSION_EXECUTION_SECONDS.labels(category=category, priority=priority).time()

def agent_call_timer(agent: str, tool: str):
    """Decorator or context manager to time an agent call."""
    return AGENT_EXECUTION_SECONDS.labels(agent=agent, tool=tool).time()

def update_registry_metrics(online_count: int):
    """Updates the online agents gauge."""
    try:
        REGISTRY_AGENTS_ONLINE.set(online_count)
    except (AttributeError, RuntimeError):
        pass

def record_healing_event(category: str, requirement: str, status: str):
    """Logs a self-healing event."""
    try:
        HEALING_EVENTS_TOTAL.labels(
            category=category,
            requirement=requirement,
            status=status
        ).inc()
    except (AttributeError, RuntimeError) as e:
        logger.debug(f"Failed to record healing event metric: {e}")

def get_metric_values() -> dict:
    """Returns current metric values as a JSON-serializable dict."""
    try:
        from prometheus_client import REGISTRY
        results = {}
        # Simple extraction of our custom metrics
        for metric in REGISTRY.collect():
            if metric.name.startswith("twisterlab_"):
                for sample in metric.samples:
                    label_str = "-".join(sample.labels.values()) if sample.labels else "value"
                    key = f"{sample.name}_{label_str}"
                    results[key] = sample.value
        return results
    except (ImportError, AttributeError, RuntimeError):
        return {}

def register_with_app(app: Any):
    pass
