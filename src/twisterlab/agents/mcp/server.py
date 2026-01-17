import asyncio
import json
import logging
import sys
from typing import Any

# Check imports gracefully for local dev where 'mcp' might not be installed yet
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    import mcp.types as types
except ImportError:
    # Fallback mock for basic syntax checking if lib missing
    print("MCP SDK missing. Install with 'pip install mcp'", file=sys.stderr)
    sys.exit(1)

from twisterlab.agents.real.browser_agent import RealBrowserAgent
from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
from twisterlab.agents.real.real_code_review_agent import RealCodeReviewAgent
from twisterlab.agents.core.maestro_agent import MaestroAgent

# Configure logging to stderr to keep stdout clean for JSON-RPC
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("twisterlab-mcp")

app = Server("twisterlab-mcp")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="browse_web",
            description="Navigate to a website using a real headless browser. Returns content and screenshot.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to visit"},
                    "screenshot": {"type": "boolean", "description": "Capture screenshot", "default": True}
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="monitor_system",
            description="Check system health metrics (CPU, RAM, Docker).",
            inputSchema={
                "type": "object",
                "properties": {
                    "detailed": {"type": "boolean", "default": False}
                }
            }
        ),
        types.Tool(
            name="analyze_code",
            description="Static analysis of code for quality and security issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to analyze"},
                    "language": {"type": "string", "default": "python"}
                },
                "required": ["code"]
            }
        ),
        types.Tool(
            name="ask_local_llm",
            description="Chat with the local LLM (Ollama) via Maestro. Useful for private tasks or using specific models.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to send"},
                    "model": {"type": "string", "default": "qwen3:8b", "description": "Local model to use"}
                },
                "required": ["message"]
            }
        ),
        types.Tool(
            name="analyze_content",
            description="Use local LLM to analyze text, logs, or data patterns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Text content to analyze"},
                    "type": {"type": "string", "enum": ["general", "data", "logs", "security"], "default": "general"}
                },
                "required": ["content"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Execute a tool."""
    logger.info(f"Executing tool: {name} with args: {arguments}")
    
    if name == "browse_web":
        url = arguments.get("url")
        screenshot = arguments.get("screenshot", True)
        
        agent = RealBrowserAgent()
        result = await agent.execute({
            "operation": "browse",
            "url": url,
            "screenshot": screenshot
        })
        
        content = []
        if result.success:
            # Add Text Summary
            title = result.data.get("title", "No Title")
            preview = result.data.get("content_preview", "")
            text_msg = f"Title: {title}\nPreview: {preview}"
            content.append(types.TextContent(type="text", text=text_msg))
            
            # Add Screenshots
            snapshots = result.data.get("snapshots", [])
            for snap in snapshots:
                if isinstance(snap, str) and "base64," in snap:
                    b64_data = snap.split("base64,")[1]
                    content.append(types.ImageContent(type="image", data=b64_data, mimeType="image/png"))
        else:
            content.append(types.TextContent(type="text", text=f"Error: {result.error}"))
            
        return content

    elif name == "monitor_system":
        detailed = arguments.get("detailed", False)
        agent = RealMonitoringAgent()
        result = await agent.execute({
            "operation": "health_check", 
            "detailed": detailed
        })
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "analyze_code":
        code = arguments.get("code")
        language = arguments.get("language", "python")
        agent = RealCodeReviewAgent()
        result = await agent.execute({
            "operation": "analyze_code",
            "code": code,
            "language": language
        })
        return [types.TextContent(type="text", text=json.dumps(result.data, indent=2))]

    elif name == "ask_local_llm":
        message = arguments.get("message")
        model = arguments.get("model", "qwen3:8b")
        agent = MaestroAgent()
        result = await agent.execute({"operation": "chat", "message": message, "model": model})
        return [types.TextContent(type="text", text=result.data.get("response", str(result)))]

    elif name == "analyze_content":
        content = arguments.get("content")
        analysis_type = arguments.get("type", "general")
        agent = MaestroAgent()
        result = await agent.execute({
            "operation": "analyze", 
            "content": content, 
            "analysis_type": analysis_type
        })
        return [types.TextContent(type="text", text=result.data.get("analysis", str(result)))]

    raise ValueError(f"Tool {name} not found")

async def main():
    # Run the server using stdin/stdout
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


class UnifiedMCPServer:
    """
    Unified MCP Server for HTTP deployment.
    
    Wraps the ToolRouter and AgentRegistry for HTTP-based MCP communication.
    """
    
    def __init__(self):
        from twisterlab.agents.mcp.router import AgentRegistry, ToolRouter
        from twisterlab.agents.registry import agent_registry
        
        # Use the global agent registry
        self._agent_registry = AgentRegistry()
        
        # Copy agents from global registry to MCP registry
        for agent_name, agent in agent_registry._agents.items():
            self._agent_registry.register_instance(agent)
        
        self._tool_router = ToolRouter(self._agent_registry)
        
        self.name = "twisterlab-mcp-unified"
        self.version = "3.2.0"
    
    def get_server_info(self) -> dict:
        """Get server information."""
        return {
            "name": self.name,
            "version": self.version,
            "agents": len(self._agent_registry.list_agents()),
            "tools": len(self._tool_router.list_tools()),
        }
    
    async def handle_request(self, rpc_request: dict) -> dict:
        """Handle JSON-RPC request."""
        method = rpc_request.get("method", "")
        params = rpc_request.get("params", {})
        req_id = rpc_request.get("id", 0)
        
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self._tool_router.list_tools()}
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await self._tool_router.execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
        elif method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": self.get_server_info(),
                    "capabilities": {"tools": {}}
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }


if __name__ == "__main__":
    asyncio.run(main())
