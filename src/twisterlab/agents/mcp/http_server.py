"""
MCP HTTP Server Wrapper

Exposes the Unified MCP Server via HTTP for K8s deployment.
Provides health checks and HTTP-based MCP communication.
"""

import logging
import os

from fastapi import FastAPI, HTTPException, Request, Response, Depends
import uvicorn
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from twisterlab.agents.mcp.server import UnifiedMCPServer
from twisterlab.api.auth import get_current_user

logging.basicConfig(
    level=getattr(logging, os.getenv("MCP_LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TwisterLab Unified MCP Server",
    description="HTTP wrapper for the MCP server",
    version="2.0.0",
)

# Global MCP server instance
mcp_server: UnifiedMCPServer = None

# Defines required roles for specific tool prefixes or exact names
# If not matched, requires authentication but no specific role (default to any auth user)
TOOL_PERMISSIONS = {
    "real-backup": ["Admin"],
    "real-resolver": ["Admin", "Support"],
    "real-classifier": ["Viewer", "Support", "Admin"],
    "sentiment-analyzer": ["Viewer", "Support", "Admin"],
    "maestro": ["Admin"],
    "database": ["Admin"],
    "code-review": ["Admin", "Operator"],
}


@app.on_event("startup")
async def startup():
    global mcp_server
    mcp_server = UnifiedMCPServer()
    logger.info(
        f"MCP Server started with {len(mcp_server._tool_router.list_tools())} tools"
    )


@app.get("/health")
async def health():
    """Health check endpoint for K8s."""
    return {
        "status": "healthy",
        "server": mcp_server.name if mcp_server else "not initialized",
        "version": mcp_server.version if mcp_server else "unknown",
        "tools": len(mcp_server._tool_router.list_tools()) if mcp_server else 0,
    }


@app.get("/")
async def root():
    """Root endpoint with server info."""
    return mcp_server.get_server_info() if mcp_server else {"error": "not initialized"}


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")
    return {"tools": mcp_server._tool_router.list_tools()}


@app.post("/tools/{tool_name}")
async def call_tool(
    tool_name: str, 
    request: Request, 
    user: dict = Depends(get_current_user)
):
    """
    Execute an MCP tool via HTTP.
    SECURED: Requires Authentication and appropriate Roles.
    """
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")

    # RBAC Check
    user_roles = user.get("roles", [])
    required_roles = None
    
    # Check permission by prefix (e.g., 'real-backup' matches 'real-backup_create_backup')
    for prefix, roles in TOOL_PERMISSIONS.items():
        if tool_name.startswith(prefix):
            required_roles = roles
            break
            
    if required_roles:
        # User must have at least one of the required roles
        if not any(role in user_roles for role in required_roles):
            logger.warning(f"Access Denied: User {user.get('sub')} ({user_roles}) tried to access {tool_name}. Required: {required_roles}")
            raise HTTPException(403, f"Access Denied. Tier '{required_roles}' required.")

    try:
        body = await request.json()
    except Exception:
        body = {}

    arguments = body.get("arguments", body)

    result = await mcp_server._tool_router.execute_tool(tool_name, arguments)

    if result.get("isError"):
        raise HTTPException(
            400, result.get("content", [{"text": "Unknown error"}])[0].get("text")
        )

    return result


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    JSON-RPC endpoint for MCP protocol.

    Allows MCP clients to communicate via HTTP instead of stdio.
    """
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")

    try:
        rpc_request = await request.json()
        response = await mcp_server.handle_request(rpc_request)
        return response or {"jsonrpc": "2.0", "result": {}}
    except Exception as e:
        logger.exception("MCP request failed")
        return {"jsonrpc": "2.0", "id": 0, "error": {"code": -32603, "message": str(e)}}


@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")
    return {"agents": mcp_server._agent_registry.list_all()}


@app.get("/stats")
async def get_stats():
    """Get router statistics."""
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")
    return mcp_server._tool_router.get_stats()


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
