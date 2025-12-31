import logging

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Guarded metric registration: attempt to create metrics and ignore if they're already registered.


def _safe_gauge(name: str, documentation: str, **kwargs):
    try:
        return Gauge(name, documentation, **kwargs)
    except ValueError:
        # Already registered — fetch existing from the REGISTRY
        logger.debug("Gauge %s already registered; reusing existing metric", name)
        # We can attempt to retrieve via internal attribute, but best to return None
        return None


def _safe_counter(name: str, documentation: str, **kwargs):
    try:
        return Counter(name, documentation, **kwargs)
    except ValueError:
        logger.debug("Counter %s already registered; reusing existing metric", name)
        return None


def register_standard_metrics():
    """Register a small set of metrics used by TwisterLab in a safe way.

    The function is idempotent and safe to call multiple times.
    """
    metrics = {}
    metrics["active_agents_count"] = _safe_gauge(
        "active_agents_count", "Number of active agents"
    )
    metrics["agent_errors_total"] = _safe_counter(
        "agent_errors_total", "Total agent errors"
    )
    return metrics


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
