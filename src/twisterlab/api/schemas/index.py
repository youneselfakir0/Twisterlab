from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict


class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None


class AgentCreate(AgentBase):
    tenantId: Optional[str] = None


class Agent(AgentBase):
    id: int


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AgentResponse(AgentBase):
    id: int
    tenantId: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HealthCheckResponse(BaseModel):
    status: str
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str


class MetricsResponse(BaseModel):
    metrics: List[Dict]
