"""
MCP HTTP Server Wrapper

Exposes the Unified MCP Server via HTTP for K8s deployment.
Provides health checks and HTTP-based MCP communication.
"""

import logging
import os

from fastapi import FastAPI, HTTPException, Request
import uvicorn

from twisterlab.agents.mcp.server import UnifiedMCPServer

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
async def call_tool(tool_name: str, request: Request):
    """Execute an MCP tool via HTTP."""
    if not mcp_server:
        raise HTTPException(500, "Server not initialized")

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


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
