"""
Unified MCP Server

Single MCP server that exposes all TwisterLab agents via the MCP protocol.
This is the main entry point for IDE integrations (Continue, Claude Desktop).
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

from twisterlab.agents.core import (
    MonitoringAgent,
    MaestroAgent,
    DatabaseAgent,
    CacheAgent,
)
from .router import AgentRegistry, ToolRouter

logger = logging.getLogger(__name__)

# MCP Protocol version
MCP_VERSION = "2024-11-05"


class UnifiedMCPServer:
    """
    Unified MCP server for TwisterLab.
    
    Exposes all agents via a single MCP endpoint using stdio transport.
    
    Features:
    - Auto-discovery of all registered agents
    - Tool routing to correct agent
    - Health monitoring
    - Graceful shutdown
    
    Usage:
        server = UnifiedMCPServer()
        await server.run()
    """
    
    def __init__(self, name: str = "twisterlab"):
        self.name = name
        self.version = "2.0.0"
        
        # Initialize registries
        self._agent_registry = AgentRegistry()
        self._tool_router: Optional[ToolRouter] = None
        self._running = False
        
        # Register default agents
        self._register_default_agents()
    
    def _register_default_agents(self) -> None:
        """Register all default TwisterLab agents."""
        self._agent_registry.register(MonitoringAgent)
        self._agent_registry.register(MaestroAgent)
        self._agent_registry.register(DatabaseAgent)
        self._agent_registry.register(CacheAgent)
        
        # Build tool router
        self._tool_router = ToolRouter(self._agent_registry)
        
        logger.info(
            f"Registered {len(self._agent_registry.list_agents())} agents "
            f"with {len(self._tool_router.list_tools())} tools"
        )
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server info for initialize response."""
        return {
            "protocolVersion": MCP_VERSION,
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
            "capabilities": {
                "tools": {
                    "listChanged": True,
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False,
                },
                "prompts": {
                    "listChanged": False,
                },
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming MCP request.
        
        Args:
            request: JSON-RPC request
            
        Returns:
            JSON-RPC response
        """
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id", 0)
        
        try:
            if method == "initialize":
                result = self.get_server_info()
                
            elif method == "notifications/initialized":
                # This is a notification, no response needed
                return None
                
            elif method == "tools/list":
                result = {
                    "tools": self._tool_router.list_tools()
                }
                
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = await self._tool_router.execute_tool(tool_name, arguments)
                
            elif method == "resources/list":
                result = {"resources": []}
                
            elif method == "prompts/list":
                result = {"prompts": []}
                
            elif method == "ping":
                result = {}
                
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }
            
        except Exception as e:
            logger.exception(f"Error handling {method}")
            return {
                "jsonrpc": "2.0",
                "id": request_id or 0,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    async def run(self) -> None:
        """
        Run the MCP server using stdio transport.
        
        Reads JSON-RPC requests from stdin and writes responses to stdout.
        """
        self._running = True
        logger.info(f"Starting {self.name} MCP server v{self.version}")
        
        # Use binary mode for Windows compatibility
        stdin = sys.stdin.buffer if hasattr(sys.stdin, 'buffer') else sys.stdin
        stdout = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout
        
        try:
            while self._running:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, stdin.readline
                )
                
                if not line:
                    break
                
                try:
                    # Decode and parse
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')
                    
                    request = json.loads(line.strip())
                    
                    # Handle request
                    response = await self.handle_request(request)
                    
                    # Write response (skip for notifications)
                    if response is not None:
                        response_line = json.dumps(response) + "\n"
                        if hasattr(stdout, 'write'):
                            if isinstance(stdout, type(sys.stdout.buffer)):
                                stdout.write(response_line.encode('utf-8'))
                            else:
                                stdout.write(response_line)
                            stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": 0,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    response_line = json.dumps(error_response) + "\n"
                    if hasattr(stdout, 'write'):
                        if isinstance(stdout, type(sys.stdout.buffer)):
                            stdout.write(response_line.encode('utf-8'))
                        else:
                            stdout.write(response_line)
                        stdout.flush()
                        
        except Exception:
            logger.exception("Server error")
        finally:
            self._running = False
            logger.info("MCP server stopped")
    
    def stop(self) -> None:
        """Stop the server."""
        self._running = False


async def main():
    """Entry point for running the unified MCP server."""
    import os
    
    # Configure logging
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,  # Log to stderr to not interfere with MCP protocol
    )
    
    server = UnifiedMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
