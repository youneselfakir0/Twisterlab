from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm

from api.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

# Prometheus metrics
try:
    from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Gauge, generate_latest

    PROMETHEUS_AVAILABLE = True
    # This is a simplified metric for this router. The main app will have more.
    active_agents = Gauge(
        "active_agents_count",
        "Number of active agents",
    )
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Import the agent registry to get real data
from agents.registry import agent_registry

router = APIRouter(
    tags=["System"],
)


@router.get("/health")
async def health_check():
    """Provides a simple health check for the API."""
    return {"status": "healthy", "version": "2.0.0", "timestamp": datetime.now().isoformat()}


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Provides a JWT token for accessing protected endpoints.
    In a real app, you would verify form_data.username and form_data.password.
    """
    user = {"username": form_data.username, "roles": ["admin"]}  # Dummy user

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "roles": user["roles"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/metrics")
async def metrics():
    """Exposes Prometheus metrics."""
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Prometheus metrics not available (prometheus_client not installed)",
        )

    # Update current active agents count from the registry
    live_agents = agent_registry.list_agents().values()
    active_count = sum(1 for agent in live_agents if agent["status"] in ["RUNNING", "IDLE"])
    active_agents.set(active_count)

    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
