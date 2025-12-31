from fastapi import APIRouter

from twisterlab.monitoring_utils import get_metric_values

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/status")
async def system_status():
    return {"status": "running", "version": "1.0.0"}


@router.get("/metrics")
async def metrics():
    # returns monitored metrics as JSON mapping metric name to current value
    vals = get_metric_values()
    return {"metrics": vals}
