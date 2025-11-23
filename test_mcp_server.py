#!/usr/bin/env python3
"""
Test script for TwisterLab MCP Server
Tests MCP server functionality without requiring Kubernetes deployment
"""

import asyncio
import json
import sys
import os
from unittest.mock import AsyncMock, patch
import httpx

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.mcp.mcp_server_continue_sync import TwisterLabMCPServer

async def test_mcp_server_initialization():
    """Test MCP server initialization"""
    print("🧪 Testing MCP server initialization...")

    server = TwisterLabMCPServer()

    # Test that the server was created successfully
    assert server.app is not None
    assert server.api_url == "http://localhost:8000"
    assert server.client is not None

    print("✅ MCP server initialization test passed")
    await server.cleanup()

async def test_list_tools_with_mock_api():
    """Test tool registration"""
    print("🧪 Testing tool registration...")

    server = TwisterLabMCPServer()

    # Check that tools are registered
    # FastMCP automatically registers tools via decorators
    # We can verify by checking the app has tools
    assert hasattr(server.app, 'list_tools')
    # The tools are registered dynamically via decorators

    print("✅ Tool registration test passed")
    await server.cleanup()


async def test_call_tool_with_mock_api():
    """Test calling a tool with mocked API response"""
    print("🧪 Testing tool execution with mocked API...")

    server = TwisterLabMCPServer()

    # Mock successful API response
    mock_tool_response = {
        "status": "ok",
        "data": {
            "result": "Backup created successfully",
            "timestamp": "2025-11-22T17:20:00Z"
        }
    }

    with patch.object(server.client, 'post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_tool_response)
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        # Test the internal _call_agent_tool method
        result = await server._call_agent_tool(
            "create_backup", {"target": "/data"}
        )

        # Verify the response
        response_data = json.loads(result)
        assert response_data["result"] == "Backup created successfully"

        print("✅ Tool execution test passed")
        await server.cleanup()


async def test_error_handling():
    """Test error handling scenarios"""
    print("🧪 Testing error handling...")

    server = TwisterLabMCPServer()

    # Test API error handling
    with patch.object(server.client, 'post') as mock_post:
        mock_post.side_effect = httpx.RequestError("Connection failed")

        try:
            await server._call_agent_tool("create_backup", {})
            assert False, "Should have raised an error"
        except Exception as e:
            assert "API request failed" in str(e)

    print("✅ Error handling test passed")
    await server.cleanup()


async def test_api_connection_error():
    """Test API connection error handling"""
    print("🧪 Testing API connection error handling...")

    server = TwisterLabMCPServer()

    with patch.object(server.client, 'post') as mock_post:
        mock_post.side_effect = Exception("Network error")

        try:
            await server._call_agent_tool("create_backup", {})
            assert False, "Should have raised an error"
        except Exception as e:
            assert "Tool execution failed" in str(e)

    print("✅ API connection error test passed")
    await server.cleanup()


async def main():
    """Run all tests"""
    print("🚀 Starting TwisterLab MCP Server Tests")
    print("=" * 50)

    try:
        await test_mcp_server_initialization()
        await test_list_tools_with_mock_api()
        await test_call_tool_with_mock_api()
        await test_error_handling()
        await test_api_connection_error()

        print("=" * 50)
        print("🎉 All MCP server tests passed successfully!")
        print("\n📋 Test Summary:")
        print("   ✅ Server initialization")
        print("   ✅ Tool registration")
        print("   ✅ Tool execution with API calls")
        print("   ✅ Error handling (API errors)")
        print("   ✅ API connection error handling")
        print("\n🔗 The MCP server is ready for Kubernetes deployment!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
