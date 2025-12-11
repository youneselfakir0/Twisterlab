import sys
from twisterlab.agents.mcp.mcp_server import MCPServerContinue

# Lightweight wrapper that reuses the MCPServerContinue implementation located at the
# repository root: mcp_server_production.py. This wrapper exists to keep backward-
# compatibility for tests and Continue IDE scripts which import
# 'src/twisterlab/agents/mcp/mcp_server_continue_sync.py'.

# Project root is 4 levels up from this file (src/twisterlab/agents/mcp)
# Keep backward-compatibility if someone executes this script directly
# (tests insert 'src' into sys.path), keep the wrapper simple and import
# the canonical package implementation above.


# Minimal CLI entrypoint to keep old invocation semantics
if __name__ == "__main__":
    # Keep a minimal CLI entrypoint to support older invocation semantics
    import json

    server = MCPServerContinue()
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            request = json.loads(raw)
            response = server.handle_request(request)
            print(json.dumps(response), flush=True)
        except Exception:
            break
