import sys
sys.path.append('src')
import importlib.util
import json

# Charger le module MCP
spec = importlib.util.spec_from_file_location('mcp_server', 'src/twisterlab/agents/mcp/mcp_server_continue_sync.py')
mcp_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_server)

def test_mcp_tools():
    """Test all MCP tools"""
    print("🧪 Testing MCP Tools")
    print("=" * 50)

    server = mcp_server.MCPServerContinue()

    # Test 1: Tools list
    print("\n1. Testing tools/list...")
    tools_response = server._handle_tools_list(1)
    tools = tools_response['result']['tools']
    print(f"✅ Found {len(tools)} tools")

    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool['name']}")

    # Test 2: Initialize
    print("\n2. Testing initialize...")
    init_params = {"clientInfo": {"name": "test-client", "version": "1.0.0"}}
    init_response = server._handle_initialize(2, init_params)
    print("✅ Initialization successful")
    print(f"   Protocol: {init_response['result']['protocolVersion']}")

    # Test 3: Test each tool with mock data
    print("\n3. Testing tool calls...")

    test_cases = [
        ("twisterlab_mcp_list_autonomous_agents", {}),
        ("monitor_system_health", {"detailed": True}),
        ("create_backup", {"backup_type": "full"}),
        ("sync_cache_db", {"force": True}),
        ("classify_ticket", {"ticket_text": "Network connectivity issue"}),
        ("resolve_ticket", {"category": "network", "description": "Cannot access internet"}),
        ("execute_command", {"command": "echo hello", "target_host": "localhost"}),
        ("configure_webui_tool", {"target_url": "https://example.com"})
    ]

    for tool_name, args in test_cases:
        print(f"\n   Testing {tool_name}...")
        try:
            # Simulate tool call
            call_params = {"name": tool_name, "arguments": args}
            response = server._handle_tools_call(3, call_params)

            if 'result' in response and 'content' in response['result']:
                content = response['result']['content']
                if content and len(content) > 0:
                    result_text = content[0].get('text', '{}')
                    try:
                        result_data = json.loads(result_text)
                        status = result_data.get('status', 'unknown')
                        print(f"     ✅ {tool_name}: {status}")
                    except:
                        print(f"     ✅ {tool_name}: response received")
                else:
                    print(f"     ⚠️  {tool_name}: empty response")
            else:
                print(f"     ❌ {tool_name}: invalid response format")

        except Exception as e:
            print(f"     ❌ {tool_name}: {str(e)}")

    print("\n🎉 MCP Tools test completed!")

if __name__ == "__main__":
    test_mcp_tools()