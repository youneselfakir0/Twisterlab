import sys
sys.path.append('src')
import importlib.util
spec = importlib.util.spec_from_file_location('mcp_server', 'src/twisterlab/agents/mcp/mcp_server_continue_sync.py')
mcp_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_server)
server = mcp_server.MCPServerContinue()
print('✅ Server initialized successfully')
print(f'Mode: {server.mode}')
print(f'API Available: {server.api_available}')
print(f'Protocol: {server.protocol_version}')
print(f'Server: {server.server_info["name"]} v{server.server_info["version"]}')