import logging

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Guarded metric registration: attempt to create metrics and ignore if they're already registered.


def _safe_gauge(name: str, documentation: str, **kwargs):
    try:
        return Gauge(name, documentation, **kwargs)
    except ValueError:
        # Already registered — fetch existing from the REGISTRY
        logger.debug("Gauge %s already registered; reusing existing metric", name)
        from prometheus_client import REGISTRY
        for metric in REGISTRY.collect():
            if metric.name == name:
                return metric
        return None


def _safe_counter(name: str, documentation: str, **kwargs):
    try:
        return Counter(name, documentation, **kwargs)
    except ValueError:
        logger.debug("Counter %s already registered; reusing existing metric", name)
        from prometheus_client import REGISTRY
        for metric in REGISTRY.collect():
            if metric.name == name:
                return metric
        return None


def _safe_histogram(name: str, documentation: str, **kwargs):
    try:
        return Histogram(name, documentation, **kwargs)
    except ValueError:
        logger.debug("Histogram %s already registered; reusing existing metric", name)
        from prometheus_client import REGISTRY
        for metric in REGISTRY.collect():
            if metric.name == name:
                return metric
        return None


def register_standard_metrics():
    """Register a small set of metrics used by TwisterLab in a safe way.

    The function is idempotent and safe to call multiple times.
    """
    metrics = {}
    
    # Agent activity metrics
    metrics["active_agents_count"] = _safe_gauge(
        "active_agents_count", 
        "Number of active agents",
        labelnames=[]
    )
    
    metrics["agent_calls_total"] = _safe_counter(
        "agent_calls_total", 
        "Total number of agent calls",
        labelnames=["agent_name", "capability"]
    )
    
    metrics["agent_errors_total"] = _safe_counter(
        "agent_errors_total", 
        "Total agent errors",
        labelnames=["agent_name", "error_type"]
    )
    
    metrics["agent_latency_seconds"] = _safe_histogram(
        "agent_latency_seconds",
        "Agent call latency in seconds",
        labelnames=["agent_name", "capability"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    )
    
    # Maestro orchestration metrics
    metrics["maestro_decisions_total"] = _safe_counter(
        "maestro_decisions_total",
        "Total decisions made by Maestro",
        labelnames=["decision_type"]
    )
    
    metrics["maestro_active_workflows"] = _safe_gauge(
        "maestro_active_workflows",
        "Number of active Maestro workflows"
    )
    
    # Ticket/Incident metrics
    metrics["tickets_resolved_total"] = _safe_counter(
        "tickets_resolved_total",
        "Total tickets resolved",
        labelnames=["resolution_type", "agent_name"]
    )
    
    metrics["ticket_resolution_time_seconds"] = _safe_histogram(
        "ticket_resolution_time_seconds",
        "Time to resolve tickets in seconds",
        labelnames=["priority"],
        buckets=(30, 60, 120, 300, 600, 1800, 3600, 7200)
    )
    
    # Command execution metrics (DesktopCommander)
    metrics["commands_executed_total"] = _safe_counter(
        "commands_executed_total",
        "Total commands executed",
        labelnames=["command_type", "status"]
    )
    
    return metrics


# Global metrics registry for easy access
_metrics_registry = None


def get_metrics():
    """Get or create the global metrics registry."""
    global _metrics_registry
    if _metrics_registry is None:
        _metrics_registry = register_standard_metrics()
    return _metrics_registry


def record_agent_call(agent_name: str, capability: str, duration: float, success: bool = True, error_type: str = None):
    """Record an agent call with timing and status."""
    metrics = get_metrics()
    
    if metrics.get("agent_calls_total"):
        metrics["agent_calls_total"].labels(agent_name=agent_name, capability=capability).inc()
    
    if metrics.get("agent_latency_seconds"):
        metrics["agent_latency_seconds"].labels(agent_name=agent_name, capability=capability).observe(duration)
    
    if not success and error_type and metrics.get("agent_errors_total"):
        metrics["agent_errors_total"].labels(agent_name=agent_name, error_type=error_type).inc()


def record_ticket_resolved(resolution_type: str, agent_name: str, resolution_time: float, priority: str = "normal"):
    """Record a resolved ticket."""
    metrics = get_metrics()
    
    if metrics.get("tickets_resolved_total"):
        metrics["tickets_resolved_total"].labels(resolution_type=resolution_type, agent_name=agent_name).inc()
    
    if metrics.get("ticket_resolution_time_seconds"):
        metrics["ticket_resolution_time_seconds"].labels(priority=priority).observe(resolution_time)


def record_command_executed(command_type: str, success: bool = True):
    """Record a command execution."""
    metrics = get_metrics()
    status = "success" if success else "failure"
    
    if metrics.get("commands_executed_total"):
        metrics["commands_executed_total"].labels(command_type=command_type, status=status).inc()


def register_with_app(app):
    # attach the register function to app for external use if needed
    app.state.twisterlab_metrics = register_standard_metrics()
    return app.state.twisterlab_metrics


def get_metric_values(metric_names: list[str] | None = None) -> dict[str, float | None]:
    """Return current metric values for requested metric names.

    If metric_names is None, return all standard metrics registered by this module.
    """
    from prometheus_client import REGISTRY

    metrics: dict[str, float | None] = {}
    if metric_names is None:
        metric_names = ["active_agents_count", "agent_errors_total"]

    for name in metric_names:
        try:
            # REGISTRY.get_sample_value returns the latest value for the metric name
            value = REGISTRY.get_sample_value(name)
            # If no value (not yet sampled), but metric exists, return 0
            metrics[name] = float(value) if value is not None else 0.0
        except Exception:
            metrics[name] = None
    return metrics
