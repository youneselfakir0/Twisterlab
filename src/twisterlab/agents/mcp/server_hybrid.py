"""
Hybrid MCP Server for Notion Integration
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, Optional

from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent as _RealMaestroAgent
from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
from twisterlab.agents.real.real_resolver_agent import RealResolverAgent
from twisterlab.agents.real.real_desktop_commander_agent import RealDesktopCommanderAgent
from twisterlab.agents.real.real_code_review_agent import RealCodeReviewAgent
from twisterlab.agents.real.real_backup_agent import RealBackupAgent
from twisterlab.agents.real.browser_agent import RealBrowserAgent
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

from twisterlab.agents.core import (
    MonitoringAgent,
    MaestroAgent,
    DatabaseAgent,
    CacheAgent,
)
from .router import AgentRegistry, ToolRouter

logger = logging.getLogger(__name__)

MCP_VERSION = "2024-11-05"

class UnifiedMCPServer:
    def __init__(self, name: str = "twisterlab"):
        self.name = name
        self.version = "2.0.0"
        self._agent_registry = AgentRegistry()
        self._tool_router: Optional[ToolRouter] = None
        self._running = False
        self._register_default_agents()
    
    def _register_default_agents(self) -> None:
        self._agent_registry.register(MonitoringAgent)
        self._agent_registry.register(_RealMaestroAgent)
        self._agent_registry.register(DatabaseAgent)
        self._agent_registry.register(CacheAgent)
        
        try:
            self._agent_registry.register(RealClassifierAgent)
            self._agent_registry.register(SentimentAnalyzerAgent)
            self._agent_registry.register(RealResolverAgent)
            self._agent_registry.register(RealDesktopCommanderAgent)
            self._agent_registry.register(RealCodeReviewAgent)
            self._agent_registry.register(RealBackupAgent)
            self._agent_registry.register(RealBrowserAgent)
            self._agent_registry.register(RealNotionAgent)
        except Exception as e:
            logger.error(f"Failed to register extended agents: {e}")
        
        self._tool_router = ToolRouter(self._agent_registry)
        maestro_agent = self._agent_registry.get_agent("maestro")
        if maestro_agent and hasattr(maestro_agent, '_inject_tool_router'):
            maestro_agent._inject_tool_router(self._tool_router)
        
        logger.info(f"Registered {len(self._agent_registry.list_agents())} agents with {len(self._tool_router.list_tools())} tools")
    
    def get_server_info(self) -> Dict[str, Any]:
        return {
            "protocolVersion": MCP_VERSION,
            "serverInfo": {"name": self.name, "version": self.version},
            "capabilities": {"tools": {"listChanged": True}}
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id", 0)
        try:
            if method == "initialize": result = self.get_server_info()
            elif method == "notifications/initialized": return None
            elif method == "tools/list": result = {"tools": self._tool_router.list_tools()}
            elif method == "tools/call":
                result = await self._tool_router.execute_tool(params.get("name", ""), params.get("arguments", {}))
            elif method in ["resources/list", "prompts/list", "ping"]: result = {}
            else: return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": request_id or 0, "error": {"code": -32603, "message": str(e)}}
    
    async def run(self) -> None:
        self._running = True
        stdin = sys.stdin.buffer if hasattr(sys.stdin, 'buffer') else sys.stdin
        stdout = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout
        try:
            while self._running:
                line = await asyncio.get_event_loop().run_in_executor(None, stdin.readline)
                if not line: break
                try:
                    if isinstance(line, bytes): line = line.decode('utf-8')
                    request = json.loads(line.strip())
                    response = await self.handle_request(request)
                    if response is not None:
                        response_line = json.dumps(response) + "\n"
                        stdout.write(response_line.encode('utf-8') if isinstance(stdout, type(sys.stdout.buffer)) else response_line)
                        stdout.flush()
                except Exception: pass
        finally: self._running = False

    def stop(self) -> None: self._running = False

async def main():
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
    logging.basicConfig(level=getattr(logging, log_level), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr)
    server = UnifiedMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
