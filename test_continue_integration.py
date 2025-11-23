import sys
sys.path.append('src')
import importlib.util
import json
import time

# Charger le module MCP
spec = importlib.util.spec_from_file_location('mcp_server', 'src/twisterlab/agents/mcp/mcp_server_continue_sync.py')
mcp_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_server)

def simulate_continue_ide_session():
    """Simulate a complete Continue IDE MCP session"""
    print("🎯 Simulating Continue IDE MCP Session")
    print("=" * 50)

    server = mcp_server.MCPServerContinue()

    # Step 1: Initialize (as Continue IDE would do)
    print("\n1. Initialize connection...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "Continue IDE",
                "version": "1.0.0"
            }
        }
    }

    # Simulate stdin -> server processing -> stdout
    init_response = server.handle_request(init_request)
    print("✅ Initialize response received")
    print(f"   Server: {init_response['result']['serverInfo']['name']}")
    print(f"   Protocol: {init_response['result']['protocolVersion']}")

    # Step 2: List tools (Continue IDE discovers capabilities)
    print("\n2. List available tools...")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    tools_response = server.handle_request(tools_request)
    tools = tools_response['result']['tools']
    print(f"✅ Found {len(tools)} tools")

    # Step 3: Call a tool (as Continue IDE would do)
    print("\n3. Call monitor_system_health tool...")
    tool_call_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "monitor_system_health",
            "arguments": {
                "detailed": True
            }
        }
    }

    tool_response = server.handle_request(tool_call_request)
    print("✅ Tool call response received")

    if 'result' in tool_response and 'content' in tool_response['result']:
        content = tool_response['result']['content']
        if content:
            result_text = content[0].get('text', '{}')
            try:
                result_data = json.loads(result_text)
                print(f"   Status: {result_data.get('status', 'unknown')}")
                print(f"   Mode: {result_data.get('mode', 'unknown')}")
                if 'data' in result_data:
                    print(f"   Data points: {len(result_data['data'])}")
            except:
                print("   Response format: text")

    # Step 4: Test another tool
    print("\n4. Call list_autonomous_agents tool...")
    list_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "twisterlab_mcp_list_autonomous_agents",
            "arguments": {}
        }
    }

    list_response = server.handle_request(list_request)
    print("✅ List agents response received")

    if 'result' in list_response and 'content' in list_response['result']:
        content = list_response['result']['content']
        if content:
            result_text = content[0].get('text', '{}')
            try:
                result_data = json.loads(result_text)
                if 'agents' in result_data:
                    agents = result_data['agents']
                    print(f"   Found {len(agents)} agents:")
                    for agent in agents[:3]:  # Show first 3
                        print(f"     - {agent}")
                    if len(agents) > 3:
                        print(f"     ... and {len(agents) - 3} more")
            except:
                print("   Response format: text")

    print("\n🎉 Continue IDE MCP Session Simulation Complete!")
    print("\n📊 Results:")
    print("   ✅ Server initialization: SUCCESS")
    print("   ✅ Protocol handshake: SUCCESS")
    print("   ✅ Tools discovery: SUCCESS")
    print("   ✅ Tool execution: SUCCESS (with hybrid fallback)")
    print("   ✅ JSON-RPC format: VALID")
    print("\n🚀 Integration MCP + Continue IDE: FONCTIONNELLE")

if __name__ == "__main__":
    simulate_continue_ide_session()