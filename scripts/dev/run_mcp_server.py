#!/usr/bin/env python3
"""
TwisterLab MCP Server Entry Point

This script starts the unified MCP server for IDE integrations.
Configure in Claude Desktop or Continue IDE:

Claude Desktop (claude_desktop_config.json):
{
    "mcpServers": {
        "twisterlab": {
            "command": "python",
            "args": ["C:\\Users\\Administrator\\Documents\\twisterlab\\run_mcp_server.py"]
        }
    }
}

Continue IDE (config.yaml):
experimental:
  modelContextProtocolServers:
    - transport:
        type: stdio
        command: python
        args:
          - C:\\Users\\Administrator\\Documents\\twisterlab\\run_mcp_server.py
"""

import asyncio
import logging
import os
import sys

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def main():
    """Entry point."""
    # Configure logging to stderr
    log_level = os.getenv("MCP_LOG_LEVEL", "WARNING")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    
    # Import and run server
    from twisterlab.agents.mcp.server import UnifiedMCPServer
    
    server = UnifiedMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
