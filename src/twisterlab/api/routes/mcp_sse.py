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
            result = await agent.execute(
                "browse",
                url=args.get("url"),
                screenshot=args.get("screenshot", True)
            )
            
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
            result = await agent.execute(
                "collect_metrics",
                detailed=args.get("detailed", False)
            )
            if result.success:
                import json
                text = json.dumps(result.data, indent=2)
                return {"content": [{"type": "text", "text": text}], "isError": False}
            else:
                return {"content": [{"type": "text", "text": f"Error: {result.error}"}], "isError": True}

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

    pubsub_task = None

    async def listen_to_redis(redis_client, s_id: str, q: asyncio.Queue):
        pubsub = redis_client.pubsub()
        channel_name = f"mcp_session:{s_id}"
        await pubsub.subscribe(channel_name)
        logger.info(f"📡 Subscribed to Redis PubSub channel: {channel_name} for SSE active stream")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    logger.debug(f"📩 SSE PubSub message received: {data}")
                    await q.put(data)
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            logger.error(f"Error in SSE PubSub listener for {s_id}: {ex}")
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()

    try:
        from twisterlab.api.auth import get_redis_client
        redis_client = await get_redis_client()
        await redis_client.ping()
        # Keep track of active session in Redis with 1 hour TTL
        await redis_client.setex(f"mcp_session_active:{session_id}", 3600, "1")
        # Start background listener task for Redis pubsub
        pubsub_task = asyncio.create_task(listen_to_redis(redis_client, session_id, queue))
        logger.info(f"✅ Redis session registered & PubSub listener started for {session_id}")
    except Exception as e:
        logger.warning(f"⚠️ Redis unavailable for SSE, falling back to pure in-memory: {e}")

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
            if pubsub_task:
                pubsub_task.cancel()
            if session_id in SESSIONS:
                del SESSIONS[session_id]
            try:
                from twisterlab.api.auth import get_redis_client
                redis_client = await get_redis_client()
                await redis_client.delete(f"mcp_session_active:{session_id}")
            except Exception:
                pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/messages")
async def handle_messages(request: Request):
    """Handle JSON-RPC messages from Claude."""
    session_id = request.query_params.get("session_id")
    if not session_id:
        return Response(status_code=400, content="Missing session_id")
    
    is_active = (session_id in SESSIONS)
    redis_active = False
    
    try:
        from twisterlab.api.auth import get_redis_client
        redis_client = await get_redis_client()
        redis_active = await redis_client.exists(f"mcp_session_active:{session_id}")
    except Exception as e:
        logger.debug(f"Redis check bypassed during message POST: {e}")

    if not is_active and not redis_active:
        logger.warning(f"❌ Session {session_id} not found in memory or Redis.")
        return Response(status_code=404, content="Session not found")
    
    try:
        body = await request.json()
        logger.debug(f"MCP Request: {body}")
        
        msg_id = body.get("id")
        method = body.get("method")
        
        response = None
        
        if method == "initialize":
            params = body.get("params", {})
            protocol_version = params.get("protocolVersion", "2025-11-25")
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": protocol_version,
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "twisterlab-pro",
                        "version": "5.0.3"
                    }
                }
            }
            
        elif method == "notifications/initialized":
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
            # 1. Direct delivery: if the session is active on this pod, deliver immediately to local memory queue
            if is_active:
                queue = SESSIONS[session_id]
                await queue.put(json.dumps(response))
                logger.info(f"📤 Pushed response directly to local memory queue for session {session_id}")
            
            # 2. Redis broadcast (best effort): send to other pods via Redis PubSub
            try:
                from twisterlab.api.auth import get_redis_client
                redis_client = await get_redis_client()
                channel_name = f"mcp_session:{session_id}"
                await redis_client.publish(channel_name, json.dumps(response))
                logger.debug(f"📡 Broadcasted response to Redis PubSub channel: {channel_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to broadcast to Redis PubSub: {e}")
            
        return Response(status_code=202)
        
    except Exception as e:
        logger.error(f"Error handling MCP message: {e}")
        return Response(status_code=500)
