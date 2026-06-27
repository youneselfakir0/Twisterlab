from __future__ import annotations
import logging
import uvicorn
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram

from twisterlab.agents.registry import get_agent_registry
from twisterlab.agents.real.real_stock_manager_agent import RealStockManagerAgent
from twisterlab.agents.real.real_order_processor_agent import RealOrderProcessorAgent

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("twisterlab.business_agents")

app = FastAPI(title="TwisterLab Business Agents Service")

# Prometheus Metrics
AGENT_REQUESTS = Counter("business_agent_requests_total", "Total requests to business agents", ["agent", "capability"])
AGENT_LATENCY = Histogram("business_agent_latency_seconds", "Latency of business agent execution", ["agent", "capability"])

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Business Agents Service...")
    # Explicitly ensure agents are registered (though registry usually handles it)
    registry = get_agent_registry()
    logger.info(f"Registered agents: {list(registry._factories.keys())}")

@app.get("/healthz")
async def health_check():
    """Liveness probe."""
    return {"status": "alive", "agents": ["stock-manager", "order-processor"]}

@app.get("/ready")
async def readiness_check():
    """Readiness probe."""
    # Here we could check connectivity to n8n if needed
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    # Entry point for the Kubernetes deployment
    uvicorn.run(app, host="0.0.0.0", port=8000)
