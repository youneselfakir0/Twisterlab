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

    raise ValueError(f"Tool {name} not found")

async def main():
    # Run the server using stdin/stdout
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
