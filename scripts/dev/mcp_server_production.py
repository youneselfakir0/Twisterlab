#!/usr/bin/env python3
"""MCP Server wrapper for Claude Desktop integration."""
import sys
import os
import json

ROOT = os.path.dirname(__file__)
SRC_DIR = os.path.join(ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from twisterlab.agents.mcp.mcp_server import MCPServerContinue


def main():
    server = MCPServerContinue()
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            request = json.loads(raw)
            response = server.handle_request(request)
            if response is not None:
                print(json.dumps(response), flush=True)
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


if __name__ == '__main__':
    main()
