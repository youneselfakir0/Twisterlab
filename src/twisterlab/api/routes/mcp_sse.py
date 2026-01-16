import asyncio
import json
import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse

# Import Agents
from twisterlab.agents.real.browser_agent import RealBrowserAgent
from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
# Add other agents imports as needed

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session store for SSE
# Maps session_id -> asyncio.Queue containing JSON strings to send
SESSIONS: Dict[str, asyncio.Queue] = {}

# ============================================================================
# MCP PROTOCOL HELPERS
# ============================================================================

async def mcp_list_tools():
    """Define available tools for Claude."""
    return {
        "tools": [
            {
                "name": "browse_web",
                "description": "Navigate to a website and capture its content and optional screenshot using a real browser.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to visit (http/https)"},
                        "screenshot": {"type": "boolean", "description": "Take a screenshot", "default": True}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "monitor_system_health",
                "description": "Check the health of the infrastructure (CPU, RAM, Docker, Disk).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "detailed": {"type": "boolean", "default": False}
                    }
                }
            }
        ]
    }

async def mcp_call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the requested tool."""
    logger.info(f"🔧 MCP Call Tool: {name} with args: {args}")
    
    try:
        if name == "browse_web":
            agent = RealBrowserAgent()
            result = await agent.execute({
                "operation": "browse",
                "url": args.get("url"),
                "screenshot": args.get("screenshot", True)
            })
            
            # Format for Claude
            content = []
            if result.success:
                # Add Text
                content.append({
                    "type": "text",
                    "text": f"Title: {result.data.get('title')}\nPreview: {result.data.get('content_preview')}"
                })
                # Add Image if present
                snapshots = result.data.get("snapshots", [])
                if snapshots:
                    # Snapshot is "data:image/png;base64,..."
                    # Claude expects pure base64 in "image" type
                    b64_data = snapshots[0].split("base64,")[1]
                    content.append({
                        "type": "image",
                        "data": b64_data,
                        "mimeType": "image/png"
                    })
                return {"content": content, "isError": False}
            else:
                return {"content": [{"type": "text", "text": f"Error: {result.error}"}], "isError": True}

        elif name == "monitor_system_health":
            agent = RealMonitoringAgent()
            result = await agent.execute({
                "operation": "health_check",
                "detailed": args.get("detailed", False)
            })
            return {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                "isError": result.get("status") != "success"
            }

        else:
            return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        return {"content": [{"type": "text", "text": f"Internal Error: {str(e)}"}], "isError": True}


# ============================================================================
# SSE ENDPOINTS
# ============================================================================

@router.get("/sse")
async def handle_sse(request: Request):
    """Establish SSE connection with Claude Desktop."""
    session_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    SESSIONS[session_id] = queue
    
    logger.info(f"🔌 New MCP SSE connection: {session_id}")

    async def event_generator():
        # 1. Send the 'endpoint' event pointing to the POST handler
        # The URL must be absolute or relative to the client. 
        # Since we are often behind K8s NodePort/Reverse Proxy, relative is safer if client supports it.
        # We assume the prefix is /api/v1/mcp if mounted there
        messages_url = f"/api/v1/mcp/messages?session_id={session_id}"
        
        yield f"event: endpoint\ndata: {messages_url}\n\n"
        
        try:
            while True:
                # Wait for messages in the queue
                if await request.is_disconnected():
                    break
                    
                # Get message from queue (JSON string)
                message = await queue.get()
                yield f"event: message\ndata: {message}\n\n"
                
        except asyncio.CancelledError:
            logger.info(f"SSE Disconnected: {session_id}")
        finally:
            if session_id in SESSIONS:
                del SESSIONS[session_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/messages")
async def handle_messages(request: Request):
    """Handle JSON-RPC messages from Claude."""
    session_id = request.query_params.get("session_id")
    if not session_id or session_id not in SESSIONS:
        return Response(status_code=404, content="Session not found")
    
    try:
        body = await request.json()
        logger.debug(f"MCP Request: {body}")
        
        msg_id = body.get("id")
        method = body.get("method")
        
        response = None
        
        if method == "notifications/initialized":
            # Just ack
            pass
            
        elif method == "ping":
            response = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            
        elif method == "tools/list":
            result = await mcp_list_tools()
            response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
            
        elif method == "tools/call":
            params = body.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            result = await mcp_call_tool(name, args)
            response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
            
        else:
            # Unknown method (like resources/list which we don't support yet)
            logger.warning(f"Unknown MCP method: {method}")
            # Don't send error for unimplemented capabilities to avoid noise, just ignore or null
            # But for RPC compliance, maybe error? Claude is permissive.
        
        if response:
            queue = SESSIONS[session_id]
            await queue.put(json.dumps(response))
            
        return Response(status_code=202)
        
    except Exception as e:
        logger.error(f"Error handling MCP message: {e}")
        return Response(status_code=500)
