#!/usr/bin/env python3
"""
MCP HTTP Proxy

Bridges stdio MCP protocol to HTTP MCP server on K3s.
This allows Continue IDE to use the remote MCP server.
"""

import sys
import json
import httpx
import asyncio
import logging

# Configuration
MCP_SERVER_URL = "http://192.168.0.30:30080"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


async def handle_request(request: dict) -> dict:
    """Forward request to HTTP MCP server."""
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "initialize":
                # Get server info
                response = await client.get(f"{MCP_SERVER_URL}/")
                data = response.json()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": data.get("name", "TwisterLab MCP"),
                            "version": data.get("version", "2.0.0"),
                        },
                        "capabilities": {
                            "tools": {"listChanged": True},
                        },
                    },
                }
            
            elif method == "tools/list":
                # Get tools from server
                response = await client.get(f"{MCP_SERVER_URL}/tools")
                data = response.json()
                tools = data.get("tools", [])
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools},
                }
            
            elif method == "tools/call":
                # Execute tool
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                response = await client.post(
                    f"{MCP_SERVER_URL}/tools/{tool_name}",
                    json={"arguments": arguments},
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result,
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32000,
                            "message": response.text,
                        },
                    }
            
            elif method == "notifications/initialized":
                # Notification, no response needed
                return None
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }
        
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": f"Cannot connect to MCP server: {e}",
                },
            }
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": str(e),
                },
            }


async def main():
    """Main loop - read from stdin, write to stdout."""
    logger.info(f"MCP HTTP Proxy started - forwarding to {MCP_SERVER_URL}")
    
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    while True:
        try:
            line = await reader.readline()
            if not line:
                break
            
            line = line.decode("utf-8").strip()
            if not line:
                continue
            
            logger.debug(f"Received: {line}")
            
            request = json.loads(line)
            response = await handle_request(request)
            
            if response:
                output = json.dumps(response)
                print(output, flush=True)
                logger.debug(f"Sent: {output}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Proxy stopped")
