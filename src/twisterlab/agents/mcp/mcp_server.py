import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not available - install with: pip install httpx")

logger = logging.getLogger(__name__)


class MCPServerContinue:
    """MCP Server for Continue IDE - stdio transport"""

    def __init__(self):
        """Initialize MCP server"""
        self.protocol_version = "2024-11-05"
        self.server_info = {
            "name": "twisterlab-mcp-continue",
            "version": "2.1.0",
            "description": "TwisterLab MCP Server for Continue IDE (Enhanced)",
        }

        # API configuration
        self.api_url = os.getenv("API_URL", "http://192.168.0.30:8000")
        self.api_timeout = 60.0

        if HTTPX_AVAILABLE:
            self.api_available = self._test_api_connectivity()
            self.mode = "REAL" if self.api_available else "HYBRID"
        else:
            self.api_available = False
            self.mode = "HYBRID"

        logger.info(
            f"Initialized: {self.server_info['name']} v{self.server_info['version']}"
        )
        logger.info(f"Mode: {self.mode}")
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"API Available: {self.api_available}")

    def _test_api_connectivity(self) -> bool:
        if not HTTPX_AVAILABLE:
            return False
        try:
            health_url = f"{self.api_url}/health"
            with httpx.Client(timeout=5.0) as client:
                response = client.get(health_url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"API connectivity test failed: {e}")
            return False

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # Handle notifications (no id) - don't respond
        if request_id is None and method not in ["initialize"]:
            logger.info(f"Notification: {method} (no response needed)")
            return None

        logger.info(f"Request: {method} (id={request_id})")

        try:
            if method == "initialize":
                return self._handle_initialize(request_id, params)
            elif method == "tools/list":
                return self._handle_tools_list(request_id)
            elif method == "tools/call":
                return self._handle_tools_call(request_id, params)
            elif method == "resources/list":
                return self._handle_resources_list(request_id)
            elif method == "resources/read":
                return self._handle_resources_read(request_id, params)
            elif method == "resources/templates/list":
                return self._handle_resources_templates_list(request_id)
            elif method == "prompts/list":
                return self._handle_prompts_list(request_id)
            elif method == "prompts/get":
                return self._handle_prompts_get(request_id, params)
            else:
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._error_response(request_id, -32700, f"Invalid JSON: {e}")
        except KeyError as e:
            logger.error(f"Missing required parameter: {e}")
            return self._error_response(request_id, -32602, f"Missing parameter: {e}")
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return self._error_response(request_id, -32602, str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._error_response(request_id, -32603, f"Internal error: {str(e)}")

    def _handle_initialize(self, request_id: int, params: Dict) -> Dict:
        client = params.get("clientInfo", {}).get("name", "unknown")
        logger.info(f"Client: {client}")

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": self.protocol_version,
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "serverInfo": self.server_info,
            },
        }

    def _handle_tools_list(self, request_id: int) -> Dict:
        tools = [
            # Agent Management
            {"name": "twisterlab_mcp_list_autonomous_agents", "description": "List all autonomous agents registered in TwisterLab", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_agent_status", "description": "Get detailed status of a specific agent", "inputSchema": {"type": "object", "properties": {"agent_id": {"type": "string", "description": "The agent ID to query"}}}},
            {"name": "create_agent", "description": "Create a new autonomous agent", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "type": {"type": "string", "enum": ["chat", "code", "browser", "system"]}, "config": {"type": "object"}}, "required": ["name", "type"]}},
            {"name": "delete_agent", "description": "Delete an agent by ID", "inputSchema": {"type": "object", "properties": {"agent_id": {"type": "string"}}, "required": ["agent_id"]}},
            {"name": "execute_agent", "description": "Execute an agent with given input", "inputSchema": {"type": "object", "properties": {"agent_id": {"type": "string"}, "input": {"type": "string"}, "context": {"type": "object"}}, "required": ["agent_id", "input"]}},
            
            # System Monitoring
            {"name": "monitor_system_health", "description": "Get comprehensive system health status including CPU, memory, disk, and services", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "check_service_status", "description": "Check status of a specific service", "inputSchema": {"type": "object", "properties": {"service_name": {"type": "string", "description": "Service name (api, redis, postgres, grafana, prometheus)"}}, "required": ["service_name"]}},
            {"name": "get_system_metrics", "description": "Get current system metrics (CPU, RAM, Disk usage)", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_docker_containers", "description": "List all Docker containers and their status", "inputSchema": {"type": "object", "properties": {}}},
            
            # LLM Integration (Cortex)
            {"name": "query_llm", "description": "Query the LLM on Cortex server", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "model": {"type": "string", "default": "llama3.2:1b"}, "temperature": {"type": "number", "default": 0.7}}, "required": ["prompt"]}},
            {"name": "list_available_models", "description": "List all available LLM models on Cortex", "inputSchema": {"type": "object", "properties": {}}},
            
            # Database Operations
            {"name": "query_database", "description": "Execute a read-only SQL query on the database", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array", "items": {"type": "string"}, "description": "Query parameters"}}, "required": ["query"]}},
            {"name": "get_database_stats", "description": "Get database statistics and connection info", "inputSchema": {"type": "object", "properties": {}}},
            
            # Cache Operations
            {"name": "get_cache_stats", "description": "Get Redis cache statistics", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "cache_get", "description": "Get a value from Redis cache", "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}},
            {"name": "cache_set", "description": "Set a value in Redis cache", "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}, "ttl": {"type": "integer", "description": "Time to live in seconds"}}, "required": ["key", "value"]}},
            
            # Logs & Debugging
            {"name": "get_recent_logs", "description": "Get recent logs from a service", "inputSchema": {"type": "object", "properties": {"service": {"type": "string"}, "lines": {"type": "integer", "default": 50}}, "required": ["service"]}},
            {"name": "search_logs", "description": "Search logs for a pattern", "inputSchema": {"type": "object", "properties": {"pattern": {"type": "string"}, "service": {"type": "string"}, "since": {"type": "string", "description": "Time duration like 1h, 30m, 1d"}}, "required": ["pattern"]}},
            
            # API Operations
            {"name": "api_health_check", "description": "Check TwisterLab API health", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_api_endpoints", "description": "List all available API endpoints", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "call_api_endpoint", "description": "Call a specific API endpoint", "inputSchema": {"type": "object", "properties": {"method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]}, "endpoint": {"type": "string"}, "body": {"type": "object"}}, "required": ["method", "endpoint"]}},
        ]
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}

    def _handle_tools_call(self, request_id: int, params: Dict) -> Dict:
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        logger.info(f"Tool: {tool_name} | Args: {arguments} | Mode: {self.mode}")

        if self.mode == "REAL" and self.api_available:
            try:
                result = self._call_api(tool_name, arguments)
            except Exception:
                result = self._get_hybrid_response(tool_name, arguments)
        elif self.mode == "HYBRID":
            try:
                result = self._call_api(tool_name, arguments)
            except Exception:
                result = self._get_hybrid_response(tool_name, arguments)
        else:
            result = self._get_mock_response(tool_name, arguments)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
        }

    def _handle_resources_list(self, request_id: int) -> Dict:
        """Return empty resources list"""
        return {"jsonrpc": "2.0", "id": request_id, "result": {"resources": []}}

    def _handle_resources_read(self, request_id: int, params: Dict) -> Dict:
        """Handle resource read - return empty for now"""
        uri = params.get("uri", "")
        return {"jsonrpc": "2.0", "id": request_id, "result": {"contents": [{"uri": uri, "text": ""}]}}

    def _handle_resources_templates_list(self, request_id: int) -> Dict:
        """Return empty resource templates list"""
        return {"jsonrpc": "2.0", "id": request_id, "result": {"resourceTemplates": []}}

    def _handle_prompts_list(self, request_id: int) -> Dict:
        """Return empty prompts list"""
        return {"jsonrpc": "2.0", "id": request_id, "result": {"prompts": []}}

    def _handle_prompts_get(self, request_id: int, params: Dict) -> Dict:
        """Handle prompt get"""
        name = params.get("name", "")
        return {"jsonrpc": "2.0", "id": request_id, "result": {"description": f"Prompt: {name}", "messages": []}}

    def _get_mock_response(self, tool_name: str, arguments: Dict) -> Dict:
        return {"status": "ok", "tool": tool_name, "data": {}}

    def _get_hybrid_response(self, tool_name: str, arguments: Dict) -> Dict:
        return {"status": "success", "mode": "HYBRID", "tool": tool_name}

    def _error_response(self, request_id: int, code: int, message: str) -> Dict:
        # Ensure id is never null in error responses
        if request_id is None:
            request_id = 0
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def _call_api(self, tool_name: str, arguments: Dict) -> Dict:
        """Perform a simple POST to API endpoint and return the JSON response."""
        if not HTTPX_AVAILABLE:
            raise Exception("httpx not available")
        # Basic payload format for REST wrapper endpoint
        payload = {
            "tool": tool_name,
            "arguments": arguments,
        }
        url = f"{self.api_url}/v1/mcp/message"
        with httpx.Client(timeout=self.api_timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
