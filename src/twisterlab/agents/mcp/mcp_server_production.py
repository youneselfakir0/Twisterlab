import logging
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI application
app = FastAPI(title="TwisterLab MCP Server", version="3.5.0")

# Security configuration via environment variables
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://localhost:8080,http://192.168.0.30:30091,http://192.168.0.30:30080"
).split(",")

# CORS configuration - restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Rate limiting middleware
try:
    from twisterlab.agents.api.security import RateLimitMiddleware
    RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT)
except ImportError:
    pass  # Security module not available

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define request and response models
class JsonRpcRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: Any


class JsonRpcResponse(BaseModel):
    jsonrpc: str
    result: Any
    id: Any


class JsonRpcError(BaseModel):
    jsonrpc: str
    error: Dict[str, Any]
    id: Any


# JSON-RPC endpoint
@app.post("/api/v1/mcp/execute")
async def execute_method(request: JsonRpcRequest):
    logger.info("Received request: %s", request.model_dump())

    # Example of handling different methods
    if request.method == "example_method":
        result = {"message": "This is an example response."}
        return JsonRpcResponse(jsonrpc="2.0", result=result, id=request.id)

    # Handle unknown method
    error_response = JsonRpcError(
        jsonrpc="2.0",
        error={"code": -32601, "message": "Method not found"},
        id=request.id,
    )
    logger.error(f"Method not found: {request.method}")
    raise HTTPException(status_code=404, detail=error_response.model_dump())


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
