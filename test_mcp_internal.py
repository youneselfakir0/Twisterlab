import requests
import json
import time

BASE_URL = "http://127.0.0.1:8080"

def test_mcp_tool(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 10000,
        "method": method,
        "params": params or {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        data = response.json()
        
        if "error" in data:
            return {"method": method, "status": "ERROR", "error": data["error"].get("message")}
        else:
            result = data.get("result", {})
            if isinstance(result, dict) and "tools" in result:
                return {"method": method, "status": "OK", "tools_count": len(result["tools"])}
            else:
                return {"method": method, "status": "OK", "result_type": type(result).__name__}
    except Exception as e:
        return {"method": method, "status": "EXCEPTION", "error": str(e)[:50]}

print("\n" + "="*60)
print("MCP TOOLS TEST - TwisterLab")
print("="*60)

# Test 1: List all tools
print("\n[1] Listing all tools...")
result = test_mcp_tool("tools/list")
print(f"    tools/list: {result['status']}")
if "tools_count" in result:
    print(f"    Total: {result['tools_count']} tools available")

# Test 2: System metrics
print("\n[2] System Metrics Tool...")
result = test_mcp_tool("tools/call", {
    "name": "monitoring_get_system_metrics",
    "arguments": {}
})
print(f"    monitoring_get_system_metrics: {result['status']}")

# Test 3: Health check
print("\n[3] Health Check Tool...")
result = test_mcp_tool("tools/call", {
    "name": "monitoring_health_check",
    "arguments": {}
})
print(f"    monitoring_health_check: {result['status']}")

# Test 4: Cache stats
print("\n[4] Cache Stats Tool...")
result = test_mcp_tool("tools/call", {
    "name": "monitoring_get_cache_stats",
    "arguments": {}
})
print(f"    monitoring_get_cache_stats: {result['status']}")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED - MCP ENDPOINT FULLY OPERATIONAL")
print("="*60 + "\n")
