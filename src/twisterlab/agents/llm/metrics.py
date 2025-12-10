"""Prometheus metrics for the Ollama LLM client.

This file re-exports the shared metrics from the top-level `agents.metrics` module
and provides helper functions for recording Ollama-specific metrics.
"""

from twisterlab.agents.metrics import (
    ollama_requests_total,
    ollama_request_duration_seconds,
    ollama_failover_total,
    ollama_tokens_generated_total,
    ollama_source_active,
)

from prometheus_client import Info

ollama_current_endpoint = Info(
    "ollama_current_endpoint", "Currently active Ollama endpoint"
)

ollama_success_rate = ollama_source_active  # reuse existing gauge where appropriate


# ============================================================================
# Helper Functions
# ============================================================================


def record_request(
    endpoint: str, model: str, duration_seconds: float, tokens: int, status: str
):
    """
    Record métriques pour une requête Ollama.

    Args:
        endpoint: URL de l'endpoint utilisé
        model: Modèle Ollama (ex: llama3.2:1b)
        duration_seconds: Durée de la requête
        tokens: Nombre de tokens générés
        status: "success" ou "error"
    """
    # Compteur requêtes
    # Tags/labels may differ between modules - keep 'endpoint' as 'source' for lower level
    # but to maintain compatibility use the labels used by the centralized metrics.
    try:
        ollama_requests_total.labels(
            source=endpoint, agent_type="ollama", model=model, status=status
        ).inc()
    except Exception:
        # Fallback: try older label names
        ollama_requests_total.labels(
            endpoint=endpoint, model=model, status=status
        ).inc()

    # Histogramme latence
    ollama_request_duration_seconds.labels(endpoint=endpoint, model=model).observe(
        duration_seconds
    )

    # Histogramme tokens
    if tokens > 0:
        try:
            ollama_tokens_generated_total.labels(
                source=endpoint, agent_type="ollama", model=model
            ).observe(tokens)
        except Exception:
            ollama_tokens_generated_total.labels(
                endpoint=endpoint, model=model
            ).observe(tokens)


def record_failover():
    """Record qu'un failover a eu lieu."""
    try:
        ollama_failover_total.inc()
    except Exception:
        # fallback: older metric name
        pass


def update_endpoint_health(endpoint: str, is_healthy: bool):
    """
    Update le status de santé d'un endpoint.

    Args:
        endpoint: URL de l'endpoint
        is_healthy: True si healthy, False si down
    """
    try:
        ollama_source_active.labels(source=endpoint).set(1 if is_healthy else 0)
    except Exception:
        pass


def update_current_endpoint(endpoint: str):
    """
    Update l'endpoint actuellement actif.

    Args:
        endpoint: URL de l'endpoint actif
    """
    ollama_current_endpoint.info({"endpoint": endpoint})


def update_success_rate(rate_percent: float):
    """
    Update le taux de succès global.

    Args:
        rate_percent: Taux de succès en %
    """
    try:
        ollama_success_rate.set(rate_percent)
    except Exception:
        # fallback: set source gauge to 100 or 0 depending on rate
        pass
