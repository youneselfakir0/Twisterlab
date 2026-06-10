#!/bin/bash
export PYTHONPATH=/home/twister/twisterlab-mcp/src
exec python3 -W ignore -m twisterlab.agents.mcp.server --silent 2>/dev/null
